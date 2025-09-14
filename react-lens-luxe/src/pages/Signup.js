import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../App';

function Signup() {
  const navigate = useNavigate();
  const { signup, error, setError } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [form, setForm] = useState({
    firstName: '',
    lastName: '',
    gender: 'female',
    age: '',
    email: '',
    phone: '',
    address: '',
    password: ''
  });

  // Clear errors when user starts typing
  React.useEffect(() => {
    setError(null);
  }, [setError]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
    if (error) setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Basic validation
    if (!form.firstName.trim() || !form.lastName.trim() || !form.email.trim() || 
        !form.phone.trim() || !form.address.trim() || !form.password) {
      setError('Please fill in all fields');
      return;
    }

    if (form.password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    if (!form.age || parseInt(form.age) < 1) {
      setError('Please enter a valid age');
      return;
    }

    setIsLoading(true);
    
    try {
      const result = await signup(form);
      
      if (result.success) {
        // Redirect to home page after successful signup
        navigate('/', { replace: true });
      }
      // Error is handled by the auth context
    } catch (error) {
      setError('Something went wrong. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="signup-container">
      <h2>Welcome to Lens&Luxe</h2>
      <p>Create an account to start your fashion journey!</p>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <form className="signup-form" onSubmit={handleSubmit}>
        <div className="form-row">
          <label>First Name</label>
          <input
            type="text"
            name="firstName"
            value={form.firstName}
            onChange={handleChange}
            required
            disabled={isLoading}
          />
        </div>

        <div className="form-row">
          <label>Last Name</label>
          <input
            type="text"
            name="lastName"
            value={form.lastName}
            onChange={handleChange}
            required
            disabled={isLoading}
          />
        </div>

        <div className="form-row">
          <label>Gender</label>
          <select 
            name="gender" 
            value={form.gender} 
            onChange={handleChange}
            disabled={isLoading}
          >
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="other">Other</option>
          </select>
        </div>

        <div className="form-row">
          <label>Age</label>
          <input
            type="number"
            name="age"
            value={form.age}
            onChange={handleChange}
            required
            min="1"
            disabled={isLoading}
          />
        </div>

        <div className="form-row">
          <label>Email</label>
          <input
            type="email"
            name="email"
            value={form.email}
            onChange={handleChange}
            required
            disabled={isLoading}
          />
        </div>

        <div className="form-row">
          <label>Phone</label>
          <input
            type="tel"
            name="phone"
            value={form.phone}
            onChange={handleChange}
            required
            disabled={isLoading}
          />
        </div>

        <div className="form-row">
          <label>Address</label>
          <input
            type="text"
            name="address"
            value={form.address}
            onChange={handleChange}
            required
            disabled={isLoading}
          />
        </div>

        <hr className="divider" />

        <div className="form-row">
          <label>Password</label>
          <input
            type="password"
            name="password"
            value={form.password}
            onChange={handleChange}
            required
            minLength={6}
            placeholder="At least 6 characters"
            disabled={isLoading}
          />
        </div>

        <button 
          type="submit" 
          className="btn-submit"
          disabled={isLoading}
        >
          {isLoading ? 'Creating Account...' : 'Sign Up'}
        </button>
      </form>

      <p className="switch-auth">
        Already have an account? <Link to="/login">Log in here</Link>
      </p>
    </div>
  );
}

export default Signup;