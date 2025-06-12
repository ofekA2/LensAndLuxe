import React from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Outlet,
  useParams
} from 'react-router-dom';
import Home from './pages/Home';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Signup from './pages/Signup';
import CategoryPage from './pages/CategoryPage';

function AuthLayout() {
  return (
    <div className="auth-layout">
      <Outlet />
    </div>
  );
}

function MainLayout() {
  return (
    <>
      <Navbar />
      <div className="main-layout">
        <Outlet />
      </div>
    </>
  );
}

function CategoryPageWrapper() {
  const { category } = useParams();
  const capitalized =
    category.charAt(0).toUpperCase() + category.slice(1);
  return <CategoryPage category={capitalized} />;
}

export default function App() {
  return (
    <Router>
      <Routes>
        <Route element={<AuthLayout />}>
          <Route path="/login"  element={<Login  />} />
          <Route path="/signup" element={<Signup />} />
        </Route>
        <Route element={<MainLayout />}>
          <Route path="/"                   element={<Home />} />
          <Route path="/category/:category" element={<CategoryPageWrapper />} />
        </Route>
      </Routes>
    </Router>
  );
}