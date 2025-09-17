import DOMPurify from 'dompurify';
import {marked} from 'marked';
import * as smd from "streaming-markdown"

interface Message {
    role: 'user' | 'bot';
    content: string;
}

interface ChatState {
    messages: Message[];
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
        // Send request to the chatbot server
        return fetch("http://localhost:8000/stream", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: message
            })
        });
    }

    private createBotMessagePlaceholder(): string {
        const messageId = `msg-${Date.now()}`;
        const messageElement = document.createElement('div');
        messageElement.id = messageId;
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

        // Get reader from the response body stream
        const reader = response.body.getReader();

        // Get the content element where we'll display the streamed response
        const contentElement = document.getElementById(`content-${messageId}`);
        const messageElement = document.getElementById(messageId);

        if (contentElement && messageElement) {
            messageElement.classList.remove('animate-pulse');
            contentElement.innerHTML = '...'; // Clear the placeholder loading animation

            try {
                // Add the complete message to state
                const completeMessage: string = await this.streamAndDecodeResponseToElement(reader, contentElement);
                if (completeMessage) {
                    this.scrollToBottom();
                    this.state.messages.push({role: 'bot', content: completeMessage});
                }
            } catch (error) {
                console.error('Error while streaming response:', error);
                contentElement.innerHTML = 'Error receiving response from server.';
            }
        }
    }

    private async streamAndDecodeResponseToElement(
        reader: ReadableStreamDefaultReader,
        contentElement: HTMLElement): Promise<string> {
        let completeMessage = '';
        const decoder = new TextDecoder();
        const renderer = smd.default_renderer(contentElement)
        const parser = smd.parser(renderer)
        while (true) {
            const {done, value} = await reader.read();
            if (done) {
                return completeMessage;
            }

            // Decode the chunk and append to complete message
            const chunk = decoder.decode(value);
            const chunkContent = parseChunk(chunk);
            if (Array.isArray(chunkContent)) {
                for (const aiEvent of chunkContent) {
                    if (aiEvent.event === 'data' && aiEvent.data !== undefined) {
                        // @ts-ignore
                        if (aiEvent.data?.error) {
                            console.error('Error event found in stream:', aiEvent.data);
                            this.displayErrorMessage("There was an error returned by the chatbot. Please try again later.", contentElement)
                            return "";
                        } else {
                            // @ts-ignore
                            const content = aiEvent.data?.content || aiEvent.data?.message || aiEvent.data;
                            console.log("found content: ", content);
                            if (completeMessage.length <= 0 || completeMessage == '...') {
                                contentElement.innerHTML = '';
                            } else {                                
                                smd.parser_write(parser, "\n");
                            }
                            if (this.containsOnlyNumbers(content)) {
                                contentElement.innerHTML += content;
                            } else {
                                smd.parser_write(parser, content.toString());
                            }
                            completeMessage += "\n" + content;
                        }
                    } else if (aiEvent.event === 'error') {
                        console.error('Error event found in stream:', aiEvent.data);
                        this.displayErrorMessage("There was an error returned by the chatbot. Please try again later.", contentElement)
                        return "";
                    } else if (aiEvent.event === 'end') {
                        return completeMessage;
                    }
                }
            }
            if (chunkContent instanceof Error) {
                console.error('Error fetching stream:', chunkContent);
                return "There was an error fetching the response. Please try again later."
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

    private addMessage(role: 'user' | 'bot', content: string): void {
        // Add message to state
        this.state.messages.push({role, content});

        // Create message element
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
                </div>
            `;
        }

        this.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
    }

    private scrollToBottom(): void {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    private startNewChat(): void {
        // Clear chat state
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
    data: unknown;
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
    data: unknown;
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