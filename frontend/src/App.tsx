import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "@/pages/Home";
import NewNovel from "@/pages/NewNovel";
import NovelWorkflow from "@/pages/NovelWorkflow";
import ErrorBoundary from "@/components/ErrorBoundary";
import ToastViewport from "@/components/ToastViewport";

export default function App() {
  return (
    <ErrorBoundary>
      <Router>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/novels/new" element={<NewNovel />} />
          <Route path="/novels/:novelId" element={<NovelWorkflow />} />
          <Route path="*" element={<Home />} />
        </Routes>
        <ToastViewport />
      </Router>
    </ErrorBoundary>
  );
}
