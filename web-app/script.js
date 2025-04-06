document.addEventListener('DOMContentLoaded', function () {
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    const micCheckbox = document.getElementById('checkbox');
    const messagesDiv = document.getElementById('messages');
    const welcomeMessage = document.getElementById('welcome-message');
    const toggleBtn = document.getElementById('toggle-btn');
    const newChatBtn = document.getElementById('new-chat-btn');
    const chatHistory = document.getElementById('chat-history');
  
    let chatCount = 1;
    let currentChatId = null;
    const chats = {};
  
    function clearMessages() {
      messagesDiv.innerHTML = '';
      welcomeMessage.style.display = 'block';
    }
  
    function addMessage(text, isUser = false, save = true) {
      const messageDiv = document.createElement('div');
      messageDiv.className = 'chat-message';
      messageDiv.style.justifyContent = isUser ? 'flex-end' : 'flex-start';
  
      const messageContent = document.createElement('p');
      messageContent.textContent = text;
      messageContent.style.background = isUser ? '#4caf50' : '#555';
      messageContent.style.color = '#fff';
  
      messageDiv.appendChild(messageContent);
      messagesDiv.appendChild(messageDiv);
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
  
      if (save && currentChatId) {
        chats[currentChatId].messages.push({ text, isUser });
      }
    }
  
    function sendMessage() {
      const text = chatInput.value.trim();
      if (text && currentChatId) {
        const currentChat = chats[currentChatId];
  
        // If this is the first message, use it as the title
        if (currentChat.messages.length === 0) {
          const title = text.split(' ').slice(0, 4).join(' ');
          currentChat.title = title;
  
          // Update the chat history list item's text
          const chatItem = [...chatHistory.children].find(
            (li) => li.dataset.chatId === currentChatId
          );
          if (chatItem) {
            chatItem.textContent = title;
            chatItem.title = title;
          }
        }
  
        addMessage(text, true);
        chatInput.value = '';
        chatInput.style.height = 'auto';
        welcomeMessage.style.display = 'none';
  
        setTimeout(() => {
          addMessage('I received your message: ' + text, false);
        }, 1000);
      }
    }
  
    function createChatSession(initialTitle = 'New chat') {
        const chatId = `chat-${Date.now()}`;
        chats[chatId] = {
          title: initialTitle,
          messages: [],
        };
        currentChatId = chatId;
      
        const li = document.createElement('li');
        li.textContent = initialTitle;
        li.dataset.chatId = chatId;
        li.title = initialTitle; // Show full title on hover
        li.addEventListener('click', () => {
          switchChat(chatId);
        });
        chatHistory.appendChild(li);
      
        clearMessages();
      }
      
  
    function switchChat(chatId) {
      if (!chats[chatId]) return;
  
      currentChatId = chatId;
      clearMessages();
      const { messages } = chats[chatId];
      messages.forEach((msg) => {
        addMessage(msg.text, msg.isUser, false);
      });
    }
  
    chatInput.addEventListener('input', () => {
      chatInput.style.height = 'auto';
      chatInput.style.height = Math.min(chatInput.scrollHeight, 150) + 'px';
    });
  
    sendButton.addEventListener('click', sendMessage);
  
    chatInput.addEventListener('keypress', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
  
    micCheckbox.addEventListener('change', function () {
      console.log(this.checked ? 'Microphone is active' : 'Microphone is inactive');
    });
  
    toggleBtn.addEventListener('click', function () {
      document.body.classList.toggle('sidebar-open');
    });
  
    newChatBtn.addEventListener('click', () => createChatSession());
  
    // Start with the first chat session
    createChatSession();
  });