import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import axios from 'axios';
import { jwtDecode } from 'jwt-decode';
import { BASE_URL } from '../config';

interface User {
    user_id: string;
    username: string;
    user_role: string;
}

interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    isHydrated: boolean;
    login: (username: string, password: string) => Promise<boolean>;
    logout: () => void;
    loading: boolean;
}

interface JwtPayload {
    sub: string; // user_id
    user_role: string;
    username: string;
    iat: number;
    exp: number;
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
    // for each reload, we need to decode jwt and hydrate user state
    const [isHydrated, setIsHydrated] = useState(false);

    // Configure axios defaults
    useEffect(() => {
        const token = localStorage.getItem('token');
    
        if (!token) {
            setIsHydrated(true);
            return;
        }
    
        try {
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
            const decoded = jwtDecode<JwtPayload>(token);
            const isJwtExpired = decoded.exp <= Date.now() / 1000;
    
            if (isJwtExpired) {
                logout();
            } else {
                setUser({
                    user_id: decoded.sub,
                    user_role: decoded.user_role,
                    username: decoded.username,
                });
            }
        } catch (e) {
            console.error("Failed to decode JWT", e);
            logout();
        } finally {
            setIsHydrated(true);
        }
    }, []);
    

    // const login = async (username: string, password: string): Promise<boolean> => {
    //     // Local (no backend)
    //     if (
    //         (username === "caregiver1" && password === "password123") ||
    //         (username === "admin" && password === "admin123")
    //     ) {
    //         const fakeUser: User = {
    //             id: "1",
    //             username,
    //             full_name: username === "admin" ? "System Admin" : "Caregiver One",
    //             role: username === "admin" ? "admin" : "caregiver",
    //         };

    //         setUser(fakeUser);
    //         localStorage.setItem("token", "fake-demo-token"); // optional
    //         return true;
    //     }
    //     return false;
    // };

    const login = async (username: string, password: string): Promise<boolean> => {
        try {
            const response = await axios.post(`${BASE_URL}/login`, {
                username,
                password,
            });

            const { jwt_token } = response.data;
            console.log(jwt_token)

            // Store token
            localStorage.setItem('token', jwt_token);
            axios.defaults.headers.common['Authorization'] = `Bearer ${jwt_token}`;

            // Decode JWT token
            const decoded = jwtDecode<JwtPayload>(jwt_token);

            // Update user state
            setUser({
                user_id: decoded.sub,
                user_role: decoded.user_role,
                username,
            });

            return true;
        } catch (error) {
            console.error('Login failed:', error);
            return false;
        }
    };

    const logout = () => {
        localStorage.removeItem('token');
        delete axios.defaults.headers.common['Authorization'];
        setUser(null);
    };

    const value: AuthContextType = {
        user,
        isAuthenticated: !!user,
        isHydrated,
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
