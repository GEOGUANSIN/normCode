import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import HomePage from './components/pages/HomePage';
import AboutPage from './components/pages/AboutPage';
import NormCodePage from './components/pages/NormCodePage';
import DemoPage from './components/pages/DemoPage';
import BlogPage from './components/pages/BlogPage';
import ContactPage from './components/pages/ContactPage';
import DocsLayout from './components/layout/DocsLayout';
import GettingStartedPage from './components/pages/docs/GettingStartedPage';
import CoreConceptsPage from './components/pages/docs/CoreConceptsPage';
import OperatorsPage from './components/pages/docs/OperatorsPage';

function App() {
  const basename = import.meta.env.PROD ? '/normCode' : '/';
  
  return (
    <Router basename={basename}>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/normcode" element={<NormCodePage />} />
          <Route path="/docs" element={<DocsLayout />}>
            <Route index element={<GettingStartedPage />} />
            <Route path="getting-started" element={<GettingStartedPage />} />
            <Route path="concepts" element={<CoreConceptsPage />} />
            <Route path="operators" element={<OperatorsPage />} />
          </Route>
          <Route path="/demo" element={<DemoPage />} />
          <Route path="/blog" element={<BlogPage />} />
          <Route path="/contact" element={<ContactPage />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App
