import tippy from 'tippy.js'
//import 'tippy.js/themes/light.css'
import 'tippy.js/themes/light-border.css'
//import 'tippy.js/themes/google.css'
//import 'tippy.js/themes/translucent.css'
import DOMPurify from 'dompurify'
import {marked} from 'marked'

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

        // Update new chat button state when waiting for response
        const updateButtonStates = () => {
            if (this.state.isWaitingForResponse) {
                this.newChatBtn.disabled = true;
            } else {
                this.newChatBtn.disabled = false;
            }
        };

        // Initial button state
        updateButtonStates();

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

        // Add user message to chat, reset UI controls
        this.state.isWaitingForResponse = true;
        this.addMessage('user', userMessage);
        this.userInput.value = '';
        this.submitBtn.disabled = true;
        this.newChatBtn.disabled = true;

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
            this.newChatBtn.disabled = false;
        }
    }

    private async sendMessageToServer(message: string): Promise<Response> {
        // Send a request to the chatbot server
        const serverUrl = import.meta.env.VITE_SERVER_URL || 'http://localhost:8000';
        return fetch(`${serverUrl}/stream`, {
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
                    const sourcingDetails = completeMessage?.example ? undefined : completeMessage.source;
                    this.addMessage('bot', completeMessage.message, sourcingDetails);
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
        messageElement: HTMLElement): Promise<{ message: string, source?: string, example?: boolean }> {
        let completeMessage: string = '';
        let buffer: string = '';
        const decoder = new TextDecoder();
        while (true) {
            const {done, value} = await reader.read();
            if (done) {
                messageElement.classList.remove('animate-pulse');
                return {message: completeMessage};
            }

            // Decode the streamed chunk and append to complete message
            buffer += decoder.decode(value, {stream: true});
            const parts: string[] = buffer.split("\n");
            buffer = '';
            while (parts.length > 0 && (!parts[parts.length - 1].startsWith('payload:') || !parts[parts.length - 1].endsWith('}'))) {
                const extra = parts.pop();
                if (buffer.length > 0) {
                    buffer = extra + "\n" + buffer;
                } else if (extra) {
                    buffer = extra;
                }
            }
            const parsedEvents = parseChunk(parts.join("\n"));
            if (Array.isArray(parsedEvents)) {
                for (const aiEvent of parsedEvents) {
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
                            const errorMessage = "There was an error returned by the chatbot. Please try again later.";
                            this.displayErrorMessage(errorMessage, contentElement)
                            return {message: errorMessage, example: true};
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
                        const errorMessage = "There was an error returned by the chatbot. Please try again later.";
                        this.displayErrorMessage(errorMessage, contentElement)
                        return {message: errorMessage, example: true};
                    } else if (aiEvent.event === 'end') {
                        return {message: completeMessage, source: aiEvent.data?.source, example: aiEvent.data?.example};
                    }
                }
            }
            if (parsedEvents instanceof Error) {
                console.error('Error fetching stream:', parsedEvents);
                return {message: "There was an error fetching the response. Please try again later.", example: true};
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
        if (!content || content.toString().trim().length == 0) {
            content = "Oops, I did not receive a response from the chatbot. Please try again.";
        }
        // @ts-ignore
        const safeHtml = DOMPurify.sanitize(marked.parse(content));
        const messageElement = document.createElement('div');
        messageElement.className = role === 'user' ? 'user-message rounded-lg p-4' : 'bot-message rounded-lg p-4';
        if (role === 'user') {
            messageElement.innerHTML = `
                <div class="flex items-start">
                    <div class="font-semibold text-blue-600 mr-2">You:</div>
                    <div class="message-content">${safeHtml}</div>
                </div>
            `;
        } else {
            messageElement.innerHTML = `
                <div class="flex items-start">
                    <div class="font-semibold text-gray-700 mr-2">Bot:</div>
                    <div class="flex-1 message-content markdown-content">
                        ${safeHtml}
                        <div class="source-icon mt-2 items-end text-nowrap"></div>
                    </div>                    
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
            // @ts-ignore
            const sourceHtml = DOMPurify.sanitize(marked.parse(source.toString()));
            tippy(sourceIcon, {
                delay: [50, 100],
                arrow: true,
                theme: 'light-border',
                trigger: 'click', // or 'focus'
                allowHTML: true,
                animation: 'fade',
                appendTo: "parent",
                content: `<div class="source-tooltip">${sourceHtml}</div>`
            });
            sourceIcon.innerHTML = `
                <a href="#" class="flex flex-nowrap text-nowrap items-end text-xs text-gray-500 hover:text-blue-500" title="Crime Sourcing + Details">
                    <span>
                        Tell me how you came up with this
                    </span>
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="ml-2 feather feather-info cursor-pointer">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="12" y1="16" x2="12" y2="12"></line>
                        <line x1="12" y1="8" x2="12.01" y2="8"></line>
                    </svg>
                </a>
            `
        } else {
            sourceIcon.innerHTML = '';
        }
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
        this.submitBtn.disabled = true;
    }
}

const parseStreamedEvent = (event: string): {
    event: 'data' | 'end' | 'error';
    session_id?: string;
    data: any;
} | undefined => {
    const regEx = /^event:\s+(?<event>[\w]+)((\r?)\n(\r?)payload: (?<data>(.|\n)*))?/gm;
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