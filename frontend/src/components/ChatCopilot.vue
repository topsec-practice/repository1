<template>
  <div>
    <button
      class="copilot-btn"
      @click="toggleSidebar"
      v-if="!visible"
      aria-label="打开天融信 AI 助手"
    >
      <svg width="28" height="28" viewBox="0 0 28 28">
        <circle cx="14" cy="14" r="14" fill="#22223B"/>
        <text x="14" y="19" text-anchor="middle" font-size="14" fill="#fff" font-family="Arial">信</text>
      </svg>
    </button>
    <transition name="slide">
      <div v-if="visible" class="copilot-sidebar">
        <div class="copilot-header">
          <span>天融信 AI 助手 · 小信</span>
          <button class="close-btn" @click="toggleSidebar" aria-label="关闭">×</button>
        </div>
        <div class="copilot-messages" ref="messages">
          <div v-if="!chatHistory.length && !streaming" class="welcome-message">
            <div class="welcome-logo">信</div>
            <p>你好，我是小信，天融信的 AI 助手。</p>
            <p class="welcome-suggestion">可以向我提问网络安全基础知识和产品文档等问题哦 ~</p>
          </div>
          <div
            v-for="(msg, idx) in chatHistory"
            :key="idx"
            :class="['copilot-message', msg.role]"
          >
            <span class="role">{{ msg.role === 'user' ? '我' : '小信' }}：</span>
            <span class="content">{{ msg.content }}</span>
          </div>
          <div v-if="streaming" class="copilot-message assistant">
            <span class="role">小信：</span>
            <span class="content">{{ streamContent }}</span>
            <span class="streaming-cursor">▋</span>
          </div>
        </div>
        <div class="copilot-input-area">
          <input
            v-model="userInput"
            @keyup.enter="sendMessage"
            :disabled="streaming"
            placeholder="问问小信…"
            class="copilot-input"
            autocomplete="off"
          />
          <button
            @click="sendMessage"
            :disabled="!userInput.trim() || streaming"
            class="send-btn"
          >发送</button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
export default {
  name: "ChatCopilot",
  data() {
    return {
      visible: false,
      userInput: "",
      chatHistory: [],
      streaming: false,
      streamContent: "",
      abortController: null,
    };
  },
  methods: {
    toggleSidebar() {
      this.visible = !this.visible;
      if (this.visible) {
        this.$nextTick(() => {
          this.scrollToBottom();
        });
      }
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const el = this.$refs.messages;
        if (el) el.scrollTop = el.scrollHeight;
      });
    },
    async sendMessage() {
      if (!this.userInput.trim() || this.streaming) return;
      const input = this.userInput.trim();
      this.chatHistory.push({ role: "user", content: input });
      this.userInput = "";
      this.streaming = true;
      this.streamContent = "";
      this.scrollToBottom();

      // 构造 payload
      const payload = { messages: this.chatHistory };
      const url = "http://127.0.0.1:16361/chat";
      this.abortController = new AbortController();

      try {
        const response = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
          signal: this.abortController.signal,
        });

        if (!response.body) throw new Error("无流式响应体");

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let done = false;
        let fullResponse = "";

        while (!done) {
          const { value, done: doneReading } = await reader.read();
          done = doneReading;
          if (value) {
            const chunk = decoder.decode(value, { stream: true });
            // 处理每一行
            chunk.split(/\r?\n/).forEach(line => {
              if (line.startsWith("data: ")) {
                try {
                  const data = JSON.parse(line.slice(6));
                  if (data.type === "content") {
                    const choices = data.choices || [];
                    if (
                      choices.length &&
                      choices[0].delta &&
                      choices[0].delta.content
                    ) {
                      const content = choices[0].delta.content;
                      this.streamContent += content;
                      fullResponse += content;
                      this.scrollToBottom();
                    }
                  }
                  if (data.type === "done") {
                    done = true;
                  }
                  if (data.type === "error") {
                    this.streamContent += "\n[错误] " + (data.error?.message || "未知错误");
                    done = true;
                  }
                } catch (e) {
                  // 忽略解析错误
                }
              }
            });
          }
        }
        // 流式结束，加入历史
        if (fullResponse) {
          this.chatHistory.push({ role: "assistant", content: fullResponse });
        }
      } catch (err) {
        this.streamContent += "\n[网络错误] " + (err.message || err);
      } finally {
        this.streaming = false;
        this.streamContent = "";
        this.abortController = null;
        this.scrollToBottom();
      }
    },
  },
};
</script>

<style scoped>
/* 新增：欢迎信息样式 */
.welcome-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: #555;
}
.welcome-logo {
  width: 60px;
  height: 60px;
  line-height: 60px;
  border-radius: 50%;
  background: #22223b;
  color: #fff;
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 20px;
}
.welcome-suggestion {
  color: #888;
  font-size: 14px;
}


/* 原有样式（稍作调整） */
.copilot-btn {
  position: fixed;
  right: 32px;
  bottom: 32px;
  z-index: 2000;
  background: #22223b;
  border: none;
  border-radius: 50%;
  width: 56px;
  height: 56px;
  box-shadow: 0 4px 16px rgba(34,34,59,0.18);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: box-shadow 0.2s;
}
.copilot-btn:hover {
  box-shadow: 0 8px 32px rgba(34,34,59,0.28);
}

.copilot-sidebar {
  position: fixed;
  top: 0;
  right: 0;
  width: 380px;
  height: 100vh;
  background: #fff;
  box-shadow: -2px 0 16px rgba(34,34,59,0.12);
  z-index: 2100;
  display: flex;
  flex-direction: column;
  animation: slideIn 0.3s;
}
@keyframes slideIn {
  from { right: -400px; }
  to { right: 0; }
}
.slide-enter-active, .slide-leave-active {
  transition: all 0.3s;
}
.slide-enter, .slide-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

.copilot-header {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  border-bottom: 1px solid #eee;
  font-weight: bold;
  font-size: 18px;
  background: #f7f7fb;
  flex-shrink: 0; /* 防止头部被压缩 */
}
.close-btn {
  background: none;
  border: none;
  font-size: 28px;
  color: #888;
  cursor: pointer;
  line-height: 1;
  padding: 0 4px;
}
.close-btn:hover {
  color: #22223b;
}

.copilot-messages {
  flex: 1;
  overflow-y: auto;
  padding: 18px 20px 12px 20px;
  background: #f9f9fb;
}
.copilot-message {
  margin-bottom: 12px;
  line-height: 1.7;
  word-break: break-word;
}
.copilot-message.user .role {
  color: #3a86ff;
  font-weight: bold;
}
.copilot-message.assistant .role {
  color: #22223b;
  font-weight: bold;
}
.copilot-message .content {
  margin-left: 4px;
}
.streaming-cursor {
  color: #3a86ff;
  animation: blink 1s steps(1) infinite;
}
@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.copilot-input-area {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-top: 1px solid #eee;
  background: #fff;
  flex-shrink: 0; /* 防止输入区被压缩 */
}
.copilot-input {
  flex: 1;
  height: 36px;
  border: 1px solid #ddd;
  border-radius: 18px;
  padding: 0 16px;
  font-size: 15px;
  outline: none;
  margin-right: 10px;
  background: #f7f7fb;
  transition: border 0.2s;
}
.copilot-input:focus {
  border: 1.5px solid #3a86ff;
}
.send-btn {
  background: #3a86ff;
  color: #fff;
  border: none;
  border-radius: 18px;
  padding: 0 18px;
  height: 36px;
  font-size: 15px;
  cursor: pointer;
  transition: background 0.2s;
}
.send-btn:disabled {
  background: #b3c7f7;
  cursor: not-allowed;
}
</style>