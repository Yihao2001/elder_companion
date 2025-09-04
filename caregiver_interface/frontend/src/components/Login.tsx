import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Login: React.FC = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const success = await login(username, password);
            if (success) {
                navigate('/dashboard');
            } else {
                setError('Invalid username or password');
            }
        } catch (err) {
            setError('Login failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-container">
            <form className="login-form" onSubmit={handleSubmit}>
                <h2>ElderComp Caregiver Login</h2>

                <div className="form-group">
                    <label htmlFor="username">Username</label>
                    <input
                        type="text"
                        id="username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        required
                        placeholder="Enter your username"
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="password">Password</label>
                    <input
                        type="password"
                        id="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        placeholder="Enter your password"
                    />
                </div>

                <button
                    type="submit"
                    className="login-button"
                    disabled={loading}
                >
                    {loading ? 'Logging in...' : 'Login'}
                </button>

                {error && <div className="error-message">{error}</div>}

                <div style={{ marginTop: '1rem', fontSize: '0.9rem', color: '#666' }}>
                    <p><strong>Demo Credentials:</strong></p>
                    <p>Username: <code>caregiver1</code> | Password: <code>password123</code></p>
                    <p>Username: <code>admin</code> | Password: <code>admin123</code></p>
                </div>
            </form>
        </div>
    );
};

export default Login;
