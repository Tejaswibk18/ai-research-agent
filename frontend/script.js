const API_URL = "http://localhost:8000";


const chatContainer =
    document.getElementById("chatContainer");

const messageInput =
    document.getElementById("messageInput");

const sendButton =
    document.getElementById("sendButton");

const newChatButton =
    document.getElementById("newChatButton");

const welcomeScreen =
    document.getElementById("welcomeScreen");


const uploadButton =
    document.getElementById("uploadButton");

const uploadChatButton =
    document.getElementById("uploadChatButton");

const fileInput =
    document.getElementById("fileInput");

const uploadModal =
    document.getElementById("uploadModal");

const closeUploadModal =
    document.getElementById("closeUploadModal");

const dropZone =
    document.getElementById("dropZone");

const uploadStatus =
    document.getElementById("uploadStatus");

const documentList =
    document.getElementById("documentList");


let isGenerating = false;


/* =========================
   CHAT
========================= */

function removeWelcomeScreen() {

    if (welcomeScreen) {
        welcomeScreen.remove();
    }
}


function createMessageElement(
    role,
    content,
    toolsUsed = []
) {

    const message =
        document.createElement("div");

    message.className =
        `message ${role}`;


    const avatar =
        document.createElement("div");

    avatar.className =
        "message-avatar";

    avatar.textContent =
        role === "user"
            ? "You"
            : "AI";


    const messageContent =
        document.createElement("div");

    messageContent.className =
        "message-content";


    const roleElement =
        document.createElement("div");

    roleElement.className =
        "message-role";

    roleElement.textContent =
        role === "user"
            ? "You"
            : "Assistant";


    const textElement =
        document.createElement("div");

    textElement.className =
        "message-text";

    textElement.textContent =
        content;


    messageContent.appendChild(
        roleElement
    );

    messageContent.appendChild(
        textElement
    );

    if (toolsUsed && toolsUsed.length > 0) {
        const toolsElement =
            document.createElement("div");

        toolsElement.className =
            "message-tools";

        toolsElement.style.fontSize = "0.85rem";
        toolsElement.style.color = "#9ba3af";
        toolsElement.style.marginTop = "8px";
        toolsElement.style.paddingTop = "8px";
        toolsElement.style.borderTop = "1px solid #2d3748";

        toolsElement.textContent =
            "Tools used: " + toolsUsed.join(", ");

        messageContent.appendChild(
            toolsElement
        );
    }


    message.appendChild(
        avatar
    );

    message.appendChild(
        messageContent
    );


    return message;
}


function addMessage(
    role,
    content,
    toolsUsed = []
) {

    removeWelcomeScreen();


    let messageList =
        document.querySelector(
            ".message-list"
        );


    if (!messageList) {

        messageList =
            document.createElement(
                "div"
            );

        messageList.className =
            "message-list";

        chatContainer.appendChild(
            messageList
        );
    }


    messageList.appendChild(
        createMessageElement(
            role,
            content,
            toolsUsed
        )
    );


    scrollToBottom();
}


function createTypingIndicator() {

    const message =
        document.createElement("div");

    message.className =
        "message assistant";

    message.id =
        "typingMessage";


    const avatar =
        document.createElement("div");

    avatar.className =
        "message-avatar";

    avatar.textContent =
        "AI";


    const content =
        document.createElement("div");

    content.className =
        "message-content";


    const role =
        document.createElement("div");

    role.className =
        "message-role";

    role.textContent =
        "Assistant";


    const typing =
        document.createElement("div");

    typing.className =
        "typing";


    for (let i = 0; i < 3; i++) {

        const dot =
            document.createElement(
                "span"
            );

        typing.appendChild(dot);
    }


    content.appendChild(role);

    content.appendChild(typing);

    message.appendChild(avatar);

    message.appendChild(content);


    return message;
}


function showTypingIndicator() {

    removeWelcomeScreen();


    let messageList =
        document.querySelector(
            ".message-list"
        );


    if (!messageList) {

        messageList =
            document.createElement(
                "div"
            );

        messageList.className =
            "message-list";

        chatContainer.appendChild(
            messageList
        );
    }


    messageList.appendChild(
        createTypingIndicator()
    );


    scrollToBottom();
}


function removeTypingIndicator() {

    const element =
        document.getElementById(
            "typingMessage"
        );


    if (element) {
        element.remove();
    }
}


function scrollToBottom() {

    chatContainer.scrollTo({
        top:
            chatContainer.scrollHeight,
        behavior: "smooth"
    });
}


async function sendMessage() {

    if (isGenerating) {
        return;
    }


    const message =
        messageInput.value.trim();


    if (!message) {
        return;
    }


    isGenerating = true;

    sendButton.disabled = true;


    addMessage(
        "user",
        message
    );


    messageInput.value = "";

    autoResize();

    showTypingIndicator();


    try {

        const response =
            await fetch(
                `${API_URL}/api/agent/run`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        message
                    })
                }
            );


        const data =
            await response.json();


        removeTypingIndicator();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Failed to generate response."
            );
        }


        addMessage(
            "assistant",
            data.response,
            data.tools_used || []
        );

    }

    catch (error) {

        removeTypingIndicator();

        addMessage(
            "assistant",
            `Error: ${error.message}`
        );

    }

    finally {

        isGenerating = false;

        sendButton.disabled = false;

        messageInput.focus();
    }
}


/* =========================
   INPUT
========================= */

function autoResize() {

    messageInput.style.height =
        "auto";


    messageInput.style.height =
        `${Math.min(
            messageInput.scrollHeight,
            180
        )}px`;
}


messageInput.addEventListener(
    "input",
    autoResize
);


messageInput.addEventListener(
    "keydown",
    event => {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            sendMessage();
        }
    }
);


sendButton.addEventListener(
    "click",
    sendMessage
);


/* =========================
   SUGGESTIONS
========================= */

document.addEventListener(
    "click",
    event => {

        const suggestion =
            event.target.closest(
                ".suggestion"
            );


        if (!suggestion) {
            return;
        }


        messageInput.value =
            suggestion.textContent.trim();


        autoResize();

        messageInput.focus();
    }
);


/* =========================
   NEW CHAT
========================= */

newChatButton.addEventListener(
    "click",
    () => {

        chatContainer.innerHTML = "";

        const welcome =
            document.createElement(
                "div"
            );

        welcome.className =
            "welcome";


        welcome.innerHTML = `
            <div class="welcome-icon">
                ✦
            </div>

            <h2>
                What can I help you research?
            </h2>

            <p>
                Upload documents and ask questions.
                Your documents will be processed,
                chunked, and converted into Gemini
                embeddings for semantic retrieval.
            </p>

            <div class="suggestions">

                <button class="suggestion">
                    Explain Transformer architecture
                </button>

                <button class="suggestion">
                    What is Retrieval-Augmented Generation?
                </button>

                <button class="suggestion">
                    Explain AI agents
                </button>

                <button class="suggestion">
                    Give me a machine learning project idea
                </button>

            </div>
        `;


        chatContainer.appendChild(
            welcome
        );


        messageInput.value = "";

        autoResize();

        messageInput.focus();
    }
);


/* =========================
   DOCUMENT UPLOAD UI
========================= */

function openUploadModal() {

    uploadModal.classList.remove(
        "hidden"
    );

    uploadStatus.textContent = "";
}


function closeUploadModalWindow() {

    uploadModal.classList.add(
        "hidden"
    );

    uploadStatus.textContent = "";

    fileInput.value = "";
}


uploadButton.addEventListener(
    "click",
    openUploadModal
);


uploadChatButton.addEventListener(
    "click",
    openUploadModal
);


closeUploadModal.addEventListener(
    "click",
    closeUploadModalWindow
);


uploadModal.addEventListener(
    "click",
    event => {

        if (
            event.target === uploadModal
        ) {

            closeUploadModalWindow();
        }
    }
);


dropZone.addEventListener(
    "click",
    () => {

        fileInput.click();
    }
);


fileInput.addEventListener(
    "change",
    event => {

        const file =
            event.target.files[0];

        if (file) {
            uploadDocument(file);
        }
    }
);


/* =========================
   DRAG & DROP
========================= */

dropZone.addEventListener(
    "dragover",
    event => {

        event.preventDefault();

        dropZone.classList.add(
            "dragging"
        );
    }
);


dropZone.addEventListener(
    "dragleave",
    () => {

        dropZone.classList.remove(
            "dragging"
        );
    }
);


dropZone.addEventListener(
    "drop",
    event => {

        event.preventDefault();

        dropZone.classList.remove(
            "dragging"
        );


        const file =
            event.dataTransfer.files[0];


        if (file) {
            uploadDocument(file);
        }
    }
);


/* =========================
   UPLOAD DOCUMENT
========================= */

async function uploadDocument(file) {

    uploadStatus.textContent =
        `Processing ${file.name}...`;


    uploadStatus.style.color =
        "#9ba3af";


    const formData =
        new FormData();

    formData.append(
        "file",
        file
    );


    try {

        const response =
            await fetch(
                `${API_URL}/api/documents/upload`,
                {
                    method: "POST",
                    body: formData
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Document upload failed."
            );
        }


        uploadStatus.textContent =
            `${file.name} processed successfully. ` +
            `${data.document.chunk_count} chunks created.`;


        uploadStatus.style.color =
            "#45d483";


        await loadDocuments();


        setTimeout(
            closeUploadModalWindow,
            1200
        );

    }

    catch (error) {

        uploadStatus.textContent =
            `Error: ${error.message}`;

        uploadStatus.style.color =
            "#ff6b6b";
    }
}


/* =========================
   DOCUMENT LIST
========================= */

function getFileExtension(
    filename
) {

    const parts =
        filename.split(".");


    if (parts.length < 2) {
        return "DOC";
    }


    return parts
        .pop()
        .toUpperCase();
}


function formatFileSize(
    bytes
) {

    if (bytes < 1024) {
        return `${bytes} B`;
    }


    if (bytes < 1024 * 1024) {
        return `${(
            bytes / 1024
        ).toFixed(1)} KB`;
    }


    return `${(
        bytes /
        (1024 * 1024)
    ).toFixed(1)} MB`;
}


function renderDocuments(
    documents
) {

    documentList.innerHTML = "";


    if (!documents.length) {

        documentList.innerHTML = `
            <div class="empty-documents">
                No documents yet
            </div>
        `;

        return;
    }


    documents.forEach(
        doc => {

            const item =
                document.createElement(
                    "div"
                );

            item.className =
                "document-item";


            item.innerHTML = `
                <div class="document-icon">
                    ${getFileExtension(
                        doc.filename
                    )}
                </div>

                <div class="document-info">

                    <div
                        class="document-name"
                        title="${escapeHtml(
                            doc.filename
                        )}"
                    >
                        ${escapeHtml(
                            doc.filename
                        )}
                    </div>

                    <div class="document-meta">
                        ${doc.chunk_count} chunks
                        ·
                        ${formatFileSize(
                            doc.size_bytes
                        )}
                    </div>

                </div>

                <button
                    class="delete-document"
                    data-id="${doc.document_id}"
                    title="Delete document"
                >
                    ×
                </button>
            `;


            documentList.appendChild(
                item
            );
        }
    );
}


function escapeHtml(
    value
) {

    return value
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


async function loadDocuments() {

    try {

        const response =
            await fetch(
                `${API_URL}/api/documents`
            );


        const data =
            await response.json();


        if (!response.ok) {
            throw new Error(
                "Failed to load documents."
            );
        }


        renderDocuments(
            data.documents
        );

    }

    catch (error) {

        documentList.innerHTML = `
            <div class="empty-documents">
                Unable to load documents
            </div>
        `;
    }
}


/* =========================
   DELETE DOCUMENT
========================= */

documentList.addEventListener(
    "click",
    async event => {

        const button =
            event.target.closest(
                ".delete-document"
            );


        if (!button) {
            return;
        }


        const documentId =
            button.dataset.id;


        try {

            const response =
                await fetch(
                    `${API_URL}/api/documents/${documentId}`,
                    {
                        method: "DELETE"
                    }
                );


            if (!response.ok) {

                const data =
                    await response.json();

                throw new Error(
                    data.detail ||
                    "Failed to delete document."
                );
            }


            await loadDocuments();

        }

        catch (error) {

            alert(
                `Error: ${error.message}`
            );
        }
    }
);


/* =========================
   INITIALIZE
========================= */

loadDocuments();

messageInput.focus();