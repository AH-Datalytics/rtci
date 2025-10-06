import DOMPurify from 'dompurify';
import {marked} from 'marked';

interface Message {
    role: 'user' | 'bot';
    content: string;
    source?: string; // Optional source information for the message
}

interface ChatState {
    messages: Message[];
    sessionId?: string;
    isWaitingForResponse: boolean;
}

class ChatApp {
    private state: ChatState;
    private chatMessages: HTMLElement;
    private userInput: HTMLTextAreaElement;
    private submitBtn: HTMLButtonElement;
    private newChatBtn: HTMLButtonElement;
    private chatForm: HTMLFormElement;

    constructor() {
        this.state = {
            messages: [],
            isWaitingForResponse: false
        };

        // Get DOM elements
        this.chatMessages = document.getElementById('chat-messages') as HTMLElement;
        this.userInput = document.getElementById('user-input') as HTMLTextAreaElement;
        this.submitBtn = document.getElementById('submit-btn') as HTMLButtonElement;
        this.newChatBtn = document.getElementById('new-chat-btn') as HTMLButtonElement;
        this.chatForm = document.getElementById('chat-form') as HTMLFormElement;

        this.setupEventListeners();
    }

    private setupEventListeners(): void {
        // Submit form
        this.chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitForm();
        });

        // New chat button
        this.newChatBtn.addEventListener('click', () => {
            this.startNewChat();
        });

        // Enable/disable submit button based on input
        this.userInput.addEventListener('input', () => {
            this.submitBtn.disabled = this.userInput.value.trim() === '' || this.state.isWaitingForResponse;
        });

        // Handle Enter key press to submit the form
        this.userInput.addEventListener('keydown', (e) => {
            // Check if the key pressed is Enter and no modifier keys are pressed
            if (e.key === 'Enter' && !e.ctrlKey && !e.altKey && !e.metaKey) {
                e.preventDefault(); // Prevent default behavior (new line)
                this.submitForm();
            }
        });

    }

    private submitForm(): void {
        this.handleUserSubmit()
            .then(() => {

            })
            .catch((ex) => {
                console.log("Unable to submit user query.", ex);
            })
    }

    private async handleUserSubmit(): Promise<void> {
        const userMessage = this.userInput.value.trim();
        if (userMessage === '' || this.state.isWaitingForResponse) return;

        // Add user message to chat
        this.addMessage('user', userMessage);
        this.userInput.value = '';

        // Set loading state
        this.state.isWaitingForResponse = true;
        this.submitBtn.disabled = true;

        try {
            // Create a placeholder for the bot's streaming response
            const botMessageId = this.createBotMessagePlaceholder();
            // Send request to server
            const response = await this.sendMessageToServer(userMessage);
            // Stream the response
            await this.streamBotResponse(response, botMessageId);
        } catch (error) {
            console.error('Error communicating with the server:', error);
            this.addMessage('bot', 'Sorry, there was an error processing your request. Please try again later.');
        } finally {
            // Reset state
            this.state.isWaitingForResponse = false;
            this.submitBtn.disabled = false;
        }
    }

    private async sendMessageToServer(message: string): Promise<Response> {
        // Send a request to the chatbot server
        return fetch("http://localhost:8000/stream", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: message,
                session_id: this.state.sessionId
            })
        });
    }

    private createBotMessagePlaceholder(): string {
        const messageId = `msg-${Date.now()}`;
        const messageElement = document.createElement('div');
        messageElement.id = `message-${messageId}`;
        messageElement.className = 'bot-message rounded-lg p-4 animate-pulse';
        messageElement.innerHTML = `
            <div class="flex items-start">
                <div class="font-semibold text-gray-700 mr-2">Bot:</div>
                <div class="message-content markdown-content" id="content-${messageId}">
                    <div class="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                    <div class="h-4 bg-gray-200 rounded w-1/2"></div>
                </div>
            </div>
        `;
        this.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
        return messageId;
    }

    private async streamBotResponse(response: Response, messageId: string): Promise<void> {
        if (!response.ok || !response.body) {
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }

        const messageElement = document.getElementById(`message-${messageId}`);
        const contentElement = document.getElementById(`content-${messageId}`);
        if (contentElement && messageElement) {
            contentElement.innerHTML = '...';
            try {
                const reader = response.body.getReader();
                const completeMessage = await this.streamAndDecodeResponseToElement(reader, contentElement, messageElement);
                if (completeMessage) {
                    messageElement.remove();
                    this.addMessage('bot', completeMessage.message, completeMessage.source);
                }
            } catch (error) {
                console.error('Error while streaming response:', error);
                contentElement.innerHTML = 'Error receiving response from server.';
            }
        }
    }

    private async streamAndDecodeResponseToElement(
        reader: ReadableStreamDefaultReader,
        contentElement: HTMLElement,
        messageElement: HTMLElement): Promise<{ message: string, source?: string }> {
        let completeMessage = '';
        const decoder = new TextDecoder();
        while (true) {
            const {done, value} = await reader.read();
            if (done) {
                messageElement.classList.remove('animate-pulse');
                return {message: completeMessage};
            }

            // Decode the chunk and append to complete message
            const chunk = decoder.decode(value);
            const chunkContent = parseChunk(chunk);
            if (Array.isArray(chunkContent)) {
                for (const aiEvent of chunkContent) {
                    if (aiEvent.event) {
                        messageElement.classList.remove('animate-pulse');
                    }
                    if (aiEvent.data?.session_id != this.state.sessionId) {
                        const updatedId = aiEvent.data?.session_id;
                        if (updatedId) {
                            this.state.sessionId = updatedId;
                        }
                    }
                    if (aiEvent.event === 'data' && aiEvent.data !== undefined) {
                        if (contentElement.innerHTML == '...') {
                            contentElement.innerHTML = '';
                        }
                        if (aiEvent.data?.error) {
                            console.error('Error event found in stream:', aiEvent.data);
                            this.displayErrorMessage("There was an error returned by the chatbot. Please try again later.", contentElement)
                            return {message: ""};
                        }
                        const content = aiEvent.data?.content || aiEvent.data?.message || aiEvent.data;
                        const type = aiEvent.data?.type;
                        const newElement = this.createStreamedContent(content, type);
                        if (newElement) {
                            contentElement.appendChild(newElement);
                            if (type == "message") {
                                completeMessage += content;
                            }
                        }
                    } else if (aiEvent.event === 'error') {
                        console.error('Error event found in stream:', aiEvent.data);
                        this.displayErrorMessage("There was an error returned by the chatbot. Please try again later.", contentElement)
                        return {message: ""};
                    } else if (aiEvent.event === 'end') {
                        return {message: completeMessage, source: aiEvent.data?.source};
                    }
                }
            }
            if (chunkContent instanceof Error) {
                console.error('Error fetching stream:', chunkContent);
                return {message: "There was an error fetching the response. Please try again later."};
            }
        }
    }

    private containsOnlyNumbers(text: string): boolean {
        const regex = /^\d+$/;
        return regex.test(text);
    }

    private displayErrorMessage(message: string, contentElement: HTMLElement): void {
        contentElement.innerHTML = "<span color='red'>" + message + "</span>"
    }

    private createStreamedContent(content: string, type?: string): HTMLElement {
        const newElement = document.createElement("div");
        if (this.containsOnlyNumbers(content)) {
            newElement.innerHTML = "<p>" + content + "</p>";
        } else {
            // @ts-ignore
            newElement.innerHTML = DOMPurify.sanitize(marked.parse(content.toString()));
        }
        if (type == "update") {
            newElement.classList.add('update-item');
        } else {
            newElement.classList.add('message-item');
        }
        return newElement
    }

    private addMessage(role: 'user' | 'bot', content: string, source?: string): void {
        this.state.messages.push({role, content, source});
        const messageElement = document.createElement('div');
        messageElement.className = role === 'user' ? 'user-message rounded-lg p-4' : 'bot-message rounded-lg p-4';
        if (role === 'user') {
            const safeHtml = DOMPurify.sanitize(content);
            messageElement.innerHTML = `
                <div class="flex items-start">
                    <div class="font-semibold text-blue-600 mr-2">You:</div>
                    <div class="message-content">${safeHtml}</div>
                </div>
            `;
        } else {
            // @ts-ignore
            const safeHtml = DOMPurify.sanitize(marked.parse(content));
            messageElement.innerHTML = `
                <div class="flex items-start">
                    <div class="font-semibold text-gray-700 mr-2">Bot:</div>
                    <div class="message-content markdown-content">${safeHtml}</div>
                    <div class="source-icon ml-4 mt-1" title="Crime Sourcing + Details"></div>
                </div>
            `;
        }

        this.chatMessages.appendChild(messageElement);
        this.updateMessageSource(messageElement, source);
        this.scrollToBottom();
    }

    private updateMessageSource(messageElement: HTMLElement, source?: string): void {
        const sourceIcon = messageElement.querySelector('.source-icon');
        if (!sourceIcon) {
            return;
        }
        if (source) {
            sourceIcon.addEventListener('click', (e) => {
                e.stopPropagation();
                this.showSourceTooltip(sourceIcon as HTMLElement, source);
            });
            sourceIcon.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-info cursor-pointer text-gray-500 hover:text-blue-500">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="16" x2="12" y2="12"></line>
                    <line x1="12" y1="8" x2="12.01" y2="8"></line>
                </svg>`
        } else {
            sourceIcon.innerHTML = '';
        }
    }

    private showSourceTooltip(iconElement: HTMLElement, source: string): void {
        // Remove any existing tooltips
        const existingTooltip = document.querySelector('.source-tooltip');
        if (existingTooltip) {
            existingTooltip.remove();
        }

        // Create tooltip element
        const tooltip = document.createElement('div');
        // @ts-ignore
        tooltip.innerHTML = DOMPurify.sanitize(marked.parse(source.toString()));
        tooltip.className = 'source-tooltip absolute bg-white p-3 rounded shadow-lg z-10 max-w-xs';

        // Position the tooltip near the icon
        const iconRect = iconElement.getBoundingClientRect();
        tooltip.style.top = `${iconRect.bottom + window.scrollY + 5}px`;
        tooltip.style.left = `${iconRect.left + window.scrollX - 100}px`;

        // Add tooltip to the DOM
        const tooltipContainer = document.getElementById('tooltip-container') as HTMLElement;
        if (tooltipContainer) {
            tooltipContainer.appendChild(tooltip);
        }

        // Close tooltip when clicking outside
        const closeTooltip = (e: MouseEvent) => {
            if (!tooltip.contains(e.target as Node) && e.target !== iconElement) {
                tooltip.remove();
                document.removeEventListener('click', closeTooltip);
            }
        };

        // Add event listener with a slight delay to prevent immediate closing
        setTimeout(() => {
            document.addEventListener('click', closeTooltip);
        }, 100);
    }

    private scrollToBottom(): void {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    private startNewChat(): void {
        // Clear chat state
        this.state.sessionId = undefined;
        this.state.messages = [];
        this.state.isWaitingForResponse = false;

        // Clear UI
        this.chatMessages.innerHTML = '';
        this.userInput.value = '';
        this.submitBtn.disabled = false;
    }
}

const parseStreamedEvent = (event: string): {
    event: 'data' | 'end' | 'error';
    session_id?: string;
    data: any;
} | undefined => {
    const regEx = /^event:\s+(?<event>[\w]+)((\r?)\n(\r?)data: (?<data>(.|\n)*))?/gm;
    const match = regEx.exec(event);
    if (!match) {
        return undefined;
    }
    const {event: eventName, data: rawData} = match.groups || {};
    if (!eventName) {
        return undefined;
    }
    if (eventName !== 'data' && eventName !== 'end' && eventName !== 'error') {
        return undefined;
    }
    try {
        const data = rawData ? JSON.parse(rawData) : undefined;
        return {event: eventName, data};
    } catch (_error) {
        return {event: eventName, data: undefined};
    }
};

const parseChunk = (chunk: string): Array<{
    event: 'data' | 'end' | 'error';
    session_id?: string;
    data: any;
}> | Error => {
    if (!chunk) {
        return [];
    }

    const regEx = /(((?<=^)|(?<=\n))event:\s+(\w+))/g;
    const eventStartPositions: number[] = [];
    let match = regEx.exec(chunk);
    while (match) {
        eventStartPositions.push(match.index);
        match = regEx.exec(chunk);
    }

    const extractEvent = (startPosition: number, index: number) => {
        const endPosition = eventStartPositions[index + 1] || chunk.length;
        return chunk.substring(startPosition, endPosition);
    };

    try {
        return eventStartPositions
            .map(extractEvent)
            .map(parseStreamedEvent)
            .filter(event => event !== undefined)
            .map(event => event!);
    } catch (_error) {
        if (_error instanceof Error) {
            return _error;
        }
        return [];
    }
};

// Initialize the app when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});