import React, { createContext, useContext, useState, useEffect } from 'react';

type Language = 'zh' | 'en';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

const translations = {
  zh: {
    // Company
    'company.name': '心镜智',
    'company.tagline': 'PsylensAI',
    
    // Navigation
    'nav.home': '首页',
    'nav.normcode': 'NormCode',
    'nav.documentation': '文档',
    'nav.demo': '演示',
    'nav.about': '关于',
    'nav.blog': '博客',
    'nav.contact': '联系我们',
    
    // Hero Section
    'hero.title': '以透明化推进AI推理',
    'hero.subtitle': '通过NormCode构建可解释AI的未来——一个革命性的框架，使AI推理透明、可控且符合人类价值观。',
    'hero.cta.primary': '探索 NormCode',
    'hero.cta.secondary': '试用演示',
    
    // Code Snippet
    'code.norm': 'norm',
    'code.transparency': 'transparency',
    'code.reasoning': 'reasoning',
    'code.explainable': 'explainable',
    'code.control': 'control',
    'code.human_aligned': 'human-aligned',
    
    // Features Section
    'features.title': '为什么选择 NormCode？',
    'features.subtitle': '构建可信AI系统的新范式',
    
    'features.transparent.title': '透明推理',
    'features.transparent.desc': '每个决策都可追溯和解释。完全了解您的AI如何得出结论，实现全程推理透明。',
    
    'features.control.title': '精细控制',
    'features.control.desc': '为您的AI定义精确的约束和规范。保持对推理过程的控制，确保与您的价值观保持一致。',
    
    'features.alignment.title': '规范对齐',
    'features.alignment.desc': '基于形式化框架，确保AI行为与指定的规范、价值观和道德准则保持一致。',
    
    'features.production.title': '生产就绪',
    'features.production.desc': '无缝集成现有系统。从原型到生产环境，具备企业级可靠性。',
    
    // Stats Section
    'stats.traceable': '可追溯推理',
    'stats.faster': '更快调试',
    'stats.blackbox': '黑盒操作',
    
    // How It Works Section
    'howitworks.title': 'NormCode 如何工作',
    'howitworks.subtitle': '实现透明AI的三个简单步骤',
    
    'howitworks.step1.title': '定义您的规范',
    'howitworks.step1.desc': '使用NormCode直观的语法指定应该管理您的AI行为的规则、价值观和约束。',
    
    'howitworks.step2.title': '构建推理链',
    'howitworks.step2.desc': '创建明确的推理路径，显示如何从前提得出结论，使每一步都可审计。',
    
    'howitworks.step3.title': '自信部署',
    'howitworks.step3.desc': '运行您的AI系统，确信每个决策都可以根据您指定的规范进行解释、调试和验证。',
    
    // Use Cases Section
    'usecases.title': '领先组织的信赖之选',
    'usecases.subtitle': '让AI在各行业实现透明化',
    
    'usecases.healthcare.title': '医疗保健',
    'usecases.healthcare.desc': '医生可以信任和验证的可解释诊断系统',
    
    'usecases.finance.title': '金融',
    'usecases.finance.desc': '可审计的决策制定，满足监管合规和风险管理',
    
    'usecases.legal.title': '法律科技',
    'usecases.legal.desc': '案例分析和法律研究的透明推理',
    
    'usecases.research.title': '研究',
    'usecases.research.desc': '具有完整记录推理路径的可重现AI实验',
    
    // CTA Section
    'cta.title': '准备好构建透明AI了吗？',
    'cta.subtitle': '加入可解释和可控人工智能的未来',
    'cta.primary': '开始使用',
    'cta.secondary': '联系我们',
    
    // Footer
    'footer.tagline': '通过 NormCode 构建透明可控的AI',
    'footer.product': '产品',
    'footer.company': '公司',
    'footer.connect': '关注我们',
    'footer.connect.desc': '构建可解释AI的未来',
    'footer.copyright': '© 2025 PsylensAI. 保留所有权利。',
  },
  en: {
    // Company
    'company.name': 'PsylensAI',
    'company.tagline': '心镜智',
    
    // Navigation
    'nav.home': 'Home',
    'nav.normcode': 'NormCode',
    'nav.documentation': 'Documentation',
    'nav.demo': 'Demo',
    'nav.about': 'About',
    'nav.blog': 'Blog',
    'nav.contact': 'Contact',
    
    // Hero Section
    'hero.title': 'Advancing AI Reasoning with Transparency',
    'hero.subtitle': 'Building the future of explainable AI through NormCode—a revolutionary framework that makes AI reasoning transparent, controllable, and aligned with human values.',
    'hero.cta.primary': 'Explore NormCode',
    'hero.cta.secondary': 'Try Live Demo',
    
    // Code Snippet
    'code.norm': 'norm',
    'code.transparency': 'transparency',
    'code.reasoning': 'reasoning',
    'code.explainable': 'explainable',
    'code.control': 'control',
    'code.human_aligned': 'human-aligned',
    
    // Features Section
    'features.title': 'Why NormCode?',
    'features.subtitle': 'A new paradigm for building trustworthy AI systems',
    
    'features.transparent.title': 'Transparent Reasoning',
    'features.transparent.desc': 'Every decision is traceable and explainable. Understand exactly how your AI arrives at conclusions with full reasoning transparency.',
    
    'features.control.title': 'Fine-Grained Control',
    'features.control.desc': 'Define precise constraints and norms for your AI. Maintain control over reasoning processes and ensure alignment with your values.',
    
    'features.alignment.title': 'Normative Alignment',
    'features.alignment.desc': 'Built on formal frameworks that ensure AI behavior aligns with specified norms, values, and ethical guidelines.',
    
    'features.production.title': 'Production Ready',
    'features.production.desc': 'Seamlessly integrate with existing systems. Scale from prototypes to production with enterprise-grade reliability.',
    
    // Stats Section
    'stats.traceable': 'Traceable Reasoning',
    'stats.faster': 'Faster Debugging',
    'stats.blackbox': 'Black Box Operations',
    
    // How It Works Section
    'howitworks.title': 'How NormCode Works',
    'howitworks.subtitle': 'Three simple steps to transparent AI',
    
    'howitworks.step1.title': 'Define Your Norms',
    'howitworks.step1.desc': 'Specify the rules, values, and constraints that should govern your AI\'s behavior using NormCode\'s intuitive syntax.',
    
    'howitworks.step2.title': 'Build Reasoning Chains',
    'howitworks.step2.desc': 'Create explicit inference pathways that show how conclusions are derived from premises, making every step auditable.',
    
    'howitworks.step3.title': 'Deploy with Confidence',
    'howitworks.step3.desc': 'Run your AI systems knowing every decision can be explained, debugged, and verified against your specified norms.',
    
    // Use Cases Section
    'usecases.title': 'Trusted by Leading Organizations',
    'usecases.subtitle': 'Making AI transparent across industries',
    
    'usecases.healthcare.title': 'Healthcare',
    'usecases.healthcare.desc': 'Explainable diagnostic systems that physicians can trust and verify',
    
    'usecases.finance.title': 'Finance',
    'usecases.finance.desc': 'Auditable decision-making for regulatory compliance and risk management',
    
    'usecases.legal.title': 'Legal Tech',
    'usecases.legal.desc': 'Transparent reasoning for case analysis and legal research',
    
    'usecases.research.title': 'Research',
    'usecases.research.desc': 'Reproducible AI experiments with fully documented reasoning paths',
    
    // CTA Section
    'cta.title': 'Ready to Build Transparent AI?',
    'cta.subtitle': 'Join the future of explainable and controllable artificial intelligence',
    'cta.primary': 'Get Started',
    'cta.secondary': 'Talk to Us',
    
    // Footer
    'footer.tagline': 'Building transparent and controllable AI through NormCode',
    'footer.product': 'Product',
    'footer.company': 'Company',
    'footer.connect': 'Connect',
    'footer.connect.desc': 'Building the future of explainable AI',
    'footer.copyright': '© 2025 PsylensAI. All rights reserved.',
  },
};

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Set Chinese as default language
  const [language, setLanguageState] = useState<Language>('zh');

  // Load language preference from localStorage
  useEffect(() => {
    const savedLanguage = localStorage.getItem('language') as Language | null;
    if (savedLanguage && (savedLanguage === 'zh' || savedLanguage === 'en')) {
      setLanguageState(savedLanguage);
    }
  }, []);

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem('language', lang);
  };

  const t = (key: string): string => {
    return translations[language][key] || key;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};

