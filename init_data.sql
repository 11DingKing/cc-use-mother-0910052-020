-- AI文章自动生成与发布系统 - 初始化测试数据
-- 运行方式: sqlite3 data/app.db < init_data.sql

-- 用户表（如果不存在）
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME
);

-- 默认管理员用户 (密码: admin123)
INSERT OR IGNORE INTO users (username, password_hash) VALUES 
('admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9');

-- 测试关键词
INSERT OR IGNORE INTO keyword (keyword) VALUES 
('人工智能'),
('机器学习'),
('深度学习'),
('自然语言处理'),
('数据分析'),
('Python编程'),
('Web开发'),
('云计算'),
('大数据'),
('区块链');

-- CMS配置 (WordPress测试环境)
-- 本地开发使用 localhost:8082，Docker部署时会自动配置为 wordpress:80
INSERT OR REPLACE INTO cms_config (id, platform, api_url, username, password, is_active) VALUES 
(1, 'wordpress', 'http://localhost:8082', 'admin', '', 1);

-- 系统配置
INSERT OR REPLACE INTO system_config (config_key, config_value) VALUES 
('generation_count', '3'),
('publish_count', '1'),
('frequency_unit', 'hour'),
('frequency_value', '1'),
('deepseek_api_key', ''),
('deepseek_api_url', 'https://api.deepseek.com/v1/chat/completions'),
('deepseek_timeout', '60');

-- 测试文章
INSERT INTO article (title, content, status, generated_at) VALUES 
('人工智能在现代企业中的应用与实践', 
'<h2>引言</h2>
<p>人工智能（AI）正在深刻改变着现代企业的运营方式。从客户服务到供应链管理，AI技术的应用范围越来越广泛。</p>

<h2>AI的核心应用场景</h2>
<p>1. <strong>智能客服</strong>：通过自然语言处理技术，实现24小时在线客户服务</p>
<p>2. <strong>数据分析</strong>：利用机器学习算法，从海量数据中挖掘商业价值</p>
<p>3. <strong>流程自动化</strong>：通过RPA技术，自动化处理重复性工作</p>

<h2>实施建议</h2>
<p>企业在引入AI技术时，应该从小规模试点开始，逐步扩大应用范围。同时要注重数据安全和隐私保护。</p>

<h2>总结</h2>
<p>人工智能是企业数字化转型的重要推动力，合理应用AI技术将为企业带来显著的竞争优势。</p>', 
'pending', datetime('now'));

INSERT INTO article (title, content, status, generated_at) VALUES 
('深度学习入门指南：从零开始掌握神经网络', 
'<h2>什么是深度学习？</h2>
<p>深度学习是机器学习的一个分支，它使用多层神经网络来学习数据的复杂模式和特征。</p>

<h2>核心概念</h2>
<p>1. <strong>神经元</strong>：深度学习的基本计算单元</p>
<p>2. <strong>层</strong>：多个神经元组成的结构</p>
<p>3. <strong>激活函数</strong>：引入非线性变换</p>
<p>4. <strong>反向传播</strong>：训练神经网络的核心算法</p>

<h2>常见框架</h2>
<p>目前主流的深度学习框架包括TensorFlow、PyTorch、Keras等，初学者建议从PyTorch开始学习。</p>

<h2>学习路径</h2>
<p>建议先掌握Python编程和线性代数基础，然后学习机器学习基础知识，最后深入深度学习领域。</p>', 
'pending', datetime('now'));

INSERT INTO article (title, content, status, generated_at) VALUES 
('Python数据分析实战：Pandas库完全指南', 
'<h2>Pandas简介</h2>
<p>Pandas是Python中最强大的数据分析库之一，提供了高效的数据结构和数据分析工具。</p>

<h2>核心数据结构</h2>
<p>1. <strong>Series</strong>：一维标签数组</p>
<p>2. <strong>DataFrame</strong>：二维表格数据结构</p>

<h2>常用操作</h2>
<p>数据读取、数据清洗、数据筛选、数据聚合、数据可视化等都是Pandas的强项。</p>

<h2>实战案例</h2>
<p>通过实际项目练习，如销售数据分析、用户行为分析等，可以快速掌握Pandas的使用技巧。</p>', 
'published', datetime('now', '-1 day'));

-- 知识库测试数据
INSERT INTO knowledge_base (file_path, file_type, content, created_at) VALUES 
('/demo/ai_introduction.txt', 'txt', 
'人工智能（Artificial Intelligence，简称AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。

AI的主要研究领域包括：
1. 机器学习：让计算机从数据中学习
2. 自然语言处理：理解和生成人类语言
3. 计算机视觉：理解和处理图像和视频
4. 专家系统：模拟人类专家的决策能力

AI的应用已经渗透到我们生活的方方面面，从智能手机的语音助手到自动驾驶汽车，从医疗诊断到金融风控。', 
datetime('now'));

INSERT INTO knowledge_base (file_path, file_type, content, created_at) VALUES 
('/demo/python_basics.txt', 'txt', 
'Python是一种高级编程语言，以其简洁易读的语法而闻名。

Python的特点：
- 简单易学：语法清晰，适合初学者
- 功能强大：拥有丰富的标准库和第三方库
- 跨平台：可在Windows、Mac、Linux上运行
- 开源免费：社区活跃，资源丰富

Python的应用领域：
1. Web开发（Django、Flask）
2. 数据科学（Pandas、NumPy）
3. 人工智能（TensorFlow、PyTorch）
4. 自动化脚本
5. 网络爬虫', 
datetime('now'));
