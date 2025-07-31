'use client';

import React, { useState } from 'react';
import axios from 'axios';
import { useRouter } from 'next/navigation';
import styles from './login.module.css';

export default function LoginPage() {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      // Random endpoint - you can change this later
      const response = await axios.post('http://localhost:8000/api/login', {
        email: formData.email,
        password: formData.password
      });

      if (response.data.access_token) {
        // Store access token if provided
        if (response.data.access_token) {
          localStorage.setItem('access_token', response.data.token);
        }
        
        console.log('Login successful:', response.data);
        
        // Redirect to main chat page
        router.push('/');
      } else {
        console.warn('Login failed:', response.data);
        setError(response.data.message || 'Login failed');
      }
    } catch (err: any) {
      console.error('Login error:', err);
      setError(err.response?.data?.message || 'Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.loginContainer}>
      <div className={styles.loginCard}>
        <div className={styles.header}>
          <h1 className={styles.title}>Welcome Back</h1>
          <p className={styles.subtitle}>Sign in to continue to LLM Chat</p>
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
          {error && (
            <div className={styles.errorMessage}>
              {error}
            </div>
          )}

          <div className={styles.inputGroup}>
            <label htmlFor="email" className={styles.label}>
              Email Address
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              className={styles.input}
              placeholder="Enter your email"
              required
            />
          </div>

          <div className={styles.inputGroup}>
            <label htmlFor="password" className={styles.label}>
              Password
            </label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              className={styles.input}
              placeholder="Enter your password"
              required
            />
          </div>

          <button
            type="submit"
            className={styles.submitButton}
            disabled={isLoading}
          >
            {isLoading ? 'Signing In...' : 'Sign In'}
          </button>
        </form>

        <div className={styles.footer}>
          <p className={styles.footerText}>
            Don't have an account? 
            <button 
              className={styles.linkButton}
              onClick={() => router.push('/register')}
            >
              Sign up here
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
