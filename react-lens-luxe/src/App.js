import React, { useState, useEffect, createContext, useContext } from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Outlet,
  useParams,
  Navigate,
  useLocation
} from 'react-router-dom';
import Home from './pages/Home';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Profile from './pages/Profile';
import CategoryPage from './pages/CategoryPage';
import { api } from "./api";


const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);


  useEffect(() => {
    checkIfLoggedIn();
  }, []);

  const checkIfLoggedIn = async () => {
    try {
      const { data } = await api.get('/api/check-auth');
      if (data?.authenticated) setUser(data.user);
    }
    catch (error) {
      console.error('Auth check failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      setError(null);
      try {
          const { data } = await api.post('/api/login', { email, password });
          setUser(data.user);
          return { success: true };
        } 
        catch (err) {
          const msg = err?.response?.data?.error || 'Login failed';
          setError(msg);
          return { success: false, error: msg };
        }
    } catch (error) {
      const errorMsg = 'Network error. Please try again.';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    }
  };

  const signup = async (userData) => {
    try {
      setError(null);
      try {
         const { data } = await api.post('/api/signup', userData);
         setUser(data.user);        
         return { success: true };
      } 
      catch (err) {
         const msg = err?.response?.data?.error || 'Signup failed';
         setError(msg);
         return { success: false, error: msg };
      }
    } catch (error) {
      const errorMsg = 'Network error. Please try again.';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    }
  };

  const logout = async () => {
    try {
      await api.post('/api/logout');
    } 
    catch (error) {
      console.error('Logout error:', error);
    } 
    finally {
      setUser(null);
    }
  };

  const value = {
    user,
    login,
    signup,
    logout,
    loading,
    error,
    setError,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}


function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        fontSize: '18px'
      }}>
        Loading...
      </div>
    );
  }

  if (!isAuthenticated) 
  {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}


function AuthLayout() {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

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
  const capitalized = category.charAt(0).toUpperCase() + category.slice(1);
  return <CategoryPage category={capitalized} />;
}

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
          </Route>

          <Route element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }>
            <Route path="/" element={<Home />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/category/:category" element={<CategoryPageWrapper />} />
          </Route>

          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}