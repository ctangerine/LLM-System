'use client';

import React, { useState } from 'react';
import axios from 'axios';
import { useRouter } from 'next/navigation';
import styles from '../login/login.module.css';

export default function RegisterPage() {
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        confirmPassword: '',
        firstName: '',
        lastName: ''
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

        // Basic validation
        if (formData.password !== formData.confirmPassword) {
            setError('Passwords do not match');
            setIsLoading(false);
            return;
        }

        try {
            // Random endpoint - you can change this later
            const response = await axios.post('http://localhost:8000/api/register', {
                email: formData.email,
                password: formData.password,
                // firstName: formData.firstName,
                // lastName: formData.lastName
            });

            if (response.data.success) {
                console.log('Registration successful:', response.data);

                // Redirect to login page
                router.push('/login');
            } else {
                setError(response.data.message || 'Registration failed');
            }
        } catch (err: any) {
            console.error('Registration error:', err);
            setError(err.response?.data?.message || 'Registration failed. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className={styles.loginContainer}>
            <div className={styles.loginCard}>
                <div className={styles.header}>
                    <h1 className={styles.title}>Create Account</h1>
                    <p className={styles.subtitle}>Sign up to get started with LLM Chat</p>
                </div>

                <form onSubmit={handleSubmit} className={styles.form}>
                    {error && (
                        <div className={styles.errorMessage}>
                            {error}
                        </div>
                    )}

                    {/* <div className={styles.nameFields}> */}
                        <div className={styles.inputGroup}>
                            <label htmlFor="firstName" className={styles.label}>
                                First Name
                            </label>
                            <input
                                type="text"
                                id="firstName"
                                name="firstName"
                                value={formData.firstName}
                                onChange={handleInputChange}
                                className={styles.input}
                                placeholder="First name"
                                required
                            />
                        </div>

                        <div className={styles.inputGroup}>
                            <label htmlFor="lastName" className={styles.label}>
                                Last Name
                            </label>
                            <input
                                type="text"
                                id="lastName"
                                name="lastName"
                                value={formData.lastName}
                                onChange={handleInputChange}
                                className={styles.input}
                                placeholder="Last name"
                                required
                            />
                        </div>
                    {/* </div> */}

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

                    <div className={styles.inputGroup}>
                        <label htmlFor="confirmPassword" className={styles.label}>
                            Confirm Password
                        </label>
                        <input
                            type="password"
                            id="confirmPassword"
                            name="confirmPassword"
                            value={formData.confirmPassword}
                            onChange={handleInputChange}
                            className={styles.input}
                            placeholder="Confirm your password"
                            required
                        />
                    </div>

                    <button
                        type="submit"
                        className={styles.submitButton}
                        disabled={isLoading}
                    >
                        {isLoading ? 'Creating Account...' : 'Create Account'}
                    </button>
                </form>

                <div className={styles.footer}>
                    <p className={styles.footerText}>
                        Already have an account?
                        <button
                            className={styles.linkButton}
                            onClick={() => router.push('/login')}
                        >
                            Sign in here
                        </button>
                    </p>
                </div>
            </div>
        </div>
    );
}
