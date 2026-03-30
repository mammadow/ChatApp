const chatRoot = document.querySelector("[data-chat-root]");

if (chatRoot) {
  const currentUsername = chatRoot.dataset.username;
  const messageLog = document.querySelector("[data-message-log]");
  const form = document.querySelector("[data-composer-form]");
  const textarea = document.querySelector("[data-message-input]");
  const sendButton = document.querySelector("[data-send-button]");
  const statusPill = document.querySelector("[data-connection-status]");
  const countLabel = document.querySelector("[data-message-count]");
  const characterCountLabel = document.querySelector("[data-character-count]");
  const composerStateLabel = document.querySelector("[data-composer-state]");
  const emptyState = document.querySelector("[data-empty-state]");
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const maxLength = Number(textarea.maxLength) || 500;
  let socket = null;
  let reconnectAttempts = 0;

  const scrollToBottom = () => {
    messageLog.scrollTop = messageLog.scrollHeight;
  };

  const isNearBottom = () =>
    messageLog.scrollHeight - messageLog.scrollTop - messageLog.clientHeight < 96;

  const refreshCount = () => {
    const count = messageLog.querySelectorAll(".message").length;
    countLabel.textContent = `${count} message${count === 1 ? "" : "s"} in view`;
    if (emptyState) {
      emptyState.hidden = count > 0;
    }
  };

  const escapeHtml = (value) =>
    value
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");

  const appendMessage = ({ username, message, timestamp }) => {
    const shouldStickToBottom = isNearBottom();
    const article = document.createElement("article");
    const modifier = username === currentUsername ? " message--self" : "";
    article.className = `message${modifier}`;
    article.innerHTML = `
      <div class="message__meta">
        <span class="message__author">${escapeHtml(username)}</span>
        <time>${escapeHtml(timestamp || "")}</time>
      </div>
      <p class="message__body">${escapeHtml(message)}</p>
    `;
    messageLog.appendChild(article);
    refreshCount();
    if (shouldStickToBottom) {
      scrollToBottom();
    }
  };

  const updateCharacterCount = () => {
    const currentLength = textarea.value.length;
    characterCountLabel.textContent = `${currentLength}/${maxLength}`;
    characterCountLabel.classList.toggle(
      "helper-emphasis",
      currentLength > Math.floor(maxLength * 0.8),
    );
  };

  const updateComposerState = () => {
    const message = textarea.value.trim();
    const connected = socket?.readyState === WebSocket.OPEN;
    sendButton.disabled = !connected || !message;
    composerStateLabel.textContent = connected
      ? "Ready to send"
      : "Waiting for connection...";
  };

  const setStatus = (label, online, helperLabel = null) => {
    statusPill.textContent = label;
    statusPill.style.background = online
      ? "rgba(31, 143, 99, 0.12)"
      : "rgba(186, 75, 34, 0.12)";
    statusPill.style.color = online ? "var(--success)" : "var(--accent-deep)";
    if (helperLabel) {
      composerStateLabel.textContent = helperLabel;
    }
    updateComposerState();
  };

  const connectSocket = () => {
    socket = new WebSocket(`${protocol}://${window.location.host}/`);
    setStatus("Connecting...", false, "Opening live connection...");

    socket.addEventListener("open", () => {
      reconnectAttempts = 0;
      setStatus("Connected", true, "Ready to send");
      textarea.focus();
    });

    socket.addEventListener("close", () => {
      reconnectAttempts += 1;
      const retryDelay = Math.min(1500 * reconnectAttempts, 6000);
      setStatus("Reconnecting...", false, `Connection lost. Retrying in ${Math.ceil(retryDelay / 1000)}s`);
      window.setTimeout(connectSocket, retryDelay);
    });

    socket.addEventListener("error", () => {
      socket.close();
    });

    socket.addEventListener("message", (event) => {
      appendMessage(JSON.parse(event.data));
      updateComposerState();
    });
  };

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const message = textarea.value.trim();
    if (!message || socket?.readyState !== WebSocket.OPEN) {
      return;
    }

    socket.send(JSON.stringify({ message }));
    textarea.value = "";
    updateCharacterCount();
    updateComposerState();
    textarea.focus();
  });

  textarea.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  textarea.addEventListener("input", () => {
    updateCharacterCount();
    updateComposerState();
  });

  connectSocket();
  updateCharacterCount();
  refreshCount();
  scrollToBottom();
  updateComposerState();
}
