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
        <text x="14" y="19" text-anchor="middle" font-size="14" fill="#fff" font-family="Arial, sans-serif">信</text>
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
            :class="['copilot-message-wrapper', msg.role, { 'error-wrapper': msg.isError }]"
          >
            <div class="copilot-message">
              <span class="role">{{ msg.role === 'user' ? '我' : '小信' }}：</span>
              <span class="content" v-html="renderMarkdown(msg.content)"></span>
            </div>
            
            <div v-if="msg.role === 'assistant' && msg.sources && msg.sources.length" class="copilot-sources-container">
              <button @click="toggleSources(msg)" class="toggle-sources-btn">
                {{ msg.sourcesVisible ? '收起引用来源' : '展开引用来源' }}
                <span :class="['arrow', { 'expanded': msg.sourcesVisible }]">›</span>
              </button>
              <transition name="fade">
                <div v-if="msg.sourcesVisible" class="copilot-sources">
                  <ul>
                    <li v-for="(source, s_idx) in msg.sources" :key="s_idx">
                      <a :href="getDownloadUrl(source.filename)" target="_blank" rel="noopener noreferrer">
                        📄 {{ source.filename }}
                      </a>
                    </li>
                  </ul>
                </div>
              </transition>
            </div>
          </div>

          <div v-if="streaming" class="copilot-message-wrapper assistant">
             <div class="copilot-message">
                <span class="role">小信：</span>
                <span class="content" v-html="renderMarkdown(streamContent)"></span>
                <span class="streaming-cursor">▋</span>
            </div>
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
      // chatHistory中的对象结构: { role, content, sources?, isError?, sourcesVisible? }
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
        this.scrollToBottom();
      }
    },

    scrollToBottom() {
      this.$nextTick(() => {
        const el = this.$refs.messages;
        if (el) el.scrollTop = el.scrollHeight;
      });
    },

    // 新增：切换引用来源的显示/隐藏
    toggleSources(message) {
        message.sourcesVisible = !message.sourcesVisible;
    },

    async sendMessage() {
      if (!this.userInput.trim() || this.streaming) return;
      
      const input = this.userInput.trim();
      this.chatHistory.push({ role: "user", content: input });
      this.userInput = "";
      this.streaming = true;
      this.streamContent = "";
      this.scrollToBottom();

      const payload = { messages: this.chatHistory.filter(m => !m.isError) }; // 不将错误消息发送给后端
      const url = "http://124.221.85.122:16361/chat";
      this.abortController = new AbortController();

      try {
        const response = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
          signal: this.abortController.signal,
        });

        if (!response.body) throw new Error("服务器未返回流式响应体");
        if (!response.ok) throw new Error(`HTTP 错误! 状态: ${response.status}`);

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let done = false;
        let fullResponse = "";
        let sources = [];

        while (!done) {
          const { value, done: doneReading } = await reader.read();
          done = doneReading;
          if (value) {
            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split(/\r?\n/).filter(line => line.startsWith("data: "));
            
            for (const line of lines) {
              try {
                const data = JSON.parse(line.slice(6));
                if (data.type === "sources") {
                  sources = data.sources || [];
                } else if (data.type === "content") {
                  const content = data.choices?.[0]?.delta?.content;
                  if (content) {
                    this.streamContent += content;
                    fullResponse += content;
                    this.scrollToBottom();
                  }
                } else if (data.type === "error") {
                  this.chatHistory.push({ role: "assistant", content: data.error?.message || "发生未知错误", isError: true });
                  done = true;
                } else if (data.type === "done") {
                  done = true;
                }
              } catch (e) {
                console.error("解析SSE数据时出错:", line, e);
              }
            }
          }
        }
        
        if (fullResponse) {
          this.chatHistory.push({ role: "assistant", content: fullResponse, sources: sources, sourcesVisible: false });
        }
      } catch (err) {
        if (err.name !== 'AbortError') {
          this.chatHistory.push({ role: "assistant", content: `网络连接失败: ${err.message}. 请检查后端服务是否正在运行。`, isError: true });
        }
      } finally {
        this.streaming = false;
        this.streamContent = "";
        this.abortController = null;
        this.scrollToBottom();
      }
    },

    getDownloadUrl(filename) {
      return `http://124.221.85.122:16361/download?filename=${encodeURIComponent(filename)}`;
    },

    renderMarkdown(text) {
      if (!text) return '';
      let html = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
      html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/__(.*?)__/g, '<strong>$1</strong>');
      html = html.replace(/\*(.*?)\*/g, '<em>$1</em>').replace(/_(.*?)_/g, '<em>$1</em>');
      html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
      html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
      html = html.replace(/\n/g, '<br>');
      return html;
    },
  },
};
</script>

<style scoped>
/* 消息区 */
.copilot-messages {
  flex: 1;
  overflow-y: auto;
  padding: 18px 20px;
  background: #fdfdfd;
}

/* 消息包装器，用于控制边距和错误状态 */
.copilot-message-wrapper {
  margin-bottom: 16px;
  padding: 12px;
  border-radius: 8px;
  background-color: #f7f7fb;
}
.copilot-message-wrapper.user {
  background-color: #e9efff;
}
/* 错误消息的红色框样式 */
.copilot-message-wrapper.error-wrapper {
  background-color: #fff2f2;
  border: 1px solid #ffcccc;
}
.error-wrapper .role {
  color: #d8000c !important;
}

.copilot-message {
  line-height: 1.7;
  word-break: break-word;
}
.copilot-message .role { font-weight: bold; }
.copilot-message.user .role { color: #3a86ff; }
.copilot-message.assistant .role { color: #22223b; }
.copilot-message .content { margin-left: 4px; }

/* 引用来源容器 */
.copilot-sources-container {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #e8eaf0;
}
.toggle-sources-btn {
  background: none;
  border: none;
  color: #555;
  cursor: pointer;
  font-size: 13px;
  font-weight: bold;
  padding: 2px 4px;
  display: flex;
  align-items: center;
}
.toggle-sources-btn .arrow {
  margin-left: 4px;
  transition: transform 0.2s;
  display: inline-block;
}
.toggle-sources-btn .arrow.expanded {
  transform: rotate(90deg);
}

/* 引用来源列表 */
.copilot-sources {
  margin-top: 8px;
}
.copilot-sources ul {
  list-style-type: none;
  padding: 0;
  margin: 0;
}
.copilot-sources li a {
  color: #3a86ff;
  text-decoration: none;
  font-size: 13px;
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  transition: background-color 0.2s;
  word-break: break-all;
}
.copilot-sources li a:hover {
  background-color: #e9efff;
  text-decoration: underline;
}

/* 过渡效果 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
  transform-origin: top;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: scaleY(0.9);
}

/* 其他样式保持不变 */
.welcome-message { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; text-align: center; color: #555; }
.welcome-logo { width: 60px; height: 60px; line-height: 60px; border-radius: 50%; background: #22223b; color: #fff; font-size: 28px; font-weight: bold; margin-bottom: 20px; }
.copilot-btn { position: fixed; right: 32px; bottom: 32px; z-index: 2000; background: #22223b; border: none; border-radius: 50%; width: 56px; height: 56px; box-shadow: 0 4px 16px rgba(34,34,59,0.18); cursor: pointer; display: flex; align-items: center; justify-content: center; }
.copilot-sidebar { position: fixed; top: 0; right: 0; width: 380px; height: 100vh; background: #fff; box-shadow: -2px 0 16px rgba(34,34,59,0.12); z-index: 2100; display: flex; flex-direction: column; }
.slide-enter-active, .slide-leave-active { transition: transform 0.3s ease; }
.slide-enter-from, .slide-leave-to { transform: translateX(100%); }
.copilot-header { height: 56px; display: flex; align-items: center; justify-content: space-between; padding: 0 20px; border-bottom: 1px solid #eee; font-weight: bold; font-size: 18px; background: #f7f7fb; flex-shrink: 0; }
.close-btn { background: none; border: none; font-size: 28px; color: #888; cursor: pointer; }
.streaming-cursor { color: #3a86ff; animation: blink 1s steps(1) infinite; }
@keyframes blink { 50% { opacity: 0; } }
.copilot-input-area { display: flex; align-items: center; padding: 12px 16px; border-top: 1px solid #eee; background: #fff; flex-shrink: 0; }
.copilot-input { flex: 1; height: 40px; border: 1px solid #ddd; border-radius: 20px; padding: 0 16px; font-size: 15px; outline: none; margin-right: 10px; background: #f7f7fb; transition: border-color 0.2s; }
.copilot-input:focus { border-color: #3a86ff; }
.send-btn { background: #3a86ff; color: #fff; border: none; border-radius: 20px; padding: 0 20px; height: 40px; font-size: 15px; cursor: pointer; font-weight: bold; transition: background-color 0.2s; }
.send-btn:disabled { background-color: #b3c7f7; cursor: not-allowed; }
</style>