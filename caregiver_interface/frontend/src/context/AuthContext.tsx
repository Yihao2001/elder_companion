import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import axios from 'axios';

interface User {
    id: string;
    username: string;
    full_name: string;
    role: string;
}

interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    login: (username: string, password: string) => Promise<boolean>;
    logout: () => void;
    loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

interface AuthProviderProps {
    children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    // Configure axios defaults
    useEffect(() => {
        const token = localStorage.getItem('token');
        if (token) {
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
            // Verify token is still valid
            checkAuthStatus();
        } else {
            setLoading(false);
        }
    }, []);

    const checkAuthStatus = async () => {
        try {
            const response = await axios.get('/auth/me');
            setUser(response.data);
        } catch (error) {
            // Token is invalid, remove it
            localStorage.removeItem('token');
            delete axios.defaults.headers.common['Authorization'];
            setUser(null);
        } finally {
            setLoading(false);
        }
    };

    const login = async (username: string, password: string): Promise<boolean> => {
        // Local (no backend)
        if (
            (username === "caregiver1" && password === "password123") ||
            (username === "admin" && password === "admin123")
        ) {
            const fakeUser: User = {
                id: "1",
                username,
                full_name: username === "admin" ? "System Admin" : "Caregiver One",
                role: username === "admin" ? "admin" : "caregiver",
            };

            setUser(fakeUser);
            localStorage.setItem("token", "fake-demo-token"); // optional
            return true;
        }
        return false;
    };


    // TO UNCOMMENT WHEN WE CONNECT TO THE BACKEND
    // const login = async (username: string, password: string): Promise<boolean> => {
    //     try {
    //         const response = await axios.post('/auth/login', {
    //             username,
    //             password,
    //         });

    //         const { access_token } = response.data;

    //         // Store token
    //         localStorage.setItem('token', access_token);
    //         axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

    //         // Get user info
    //         const userResponse = await axios.get('/auth/me');
    //         setUser(userResponse.data);

    //         return true;
    //     } catch (error) {
    //         console.error('Login failed:', error);
    //         return false;
    //     }
    // };

    const logout = () => {
        localStorage.removeItem('token');
        delete axios.defaults.headers.common['Authorization'];
        setUser(null);
    };

    const value: AuthContextType = {
        user,
        isAuthenticated: !!user,
        login,
        logout,
        loading,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};
