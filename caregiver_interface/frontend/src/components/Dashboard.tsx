import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

interface DashboardStats {
    totalElderly: number;
    totalPreferences: number;
    totalMedicalRecords: number;
}

const Dashboard: React.FC = () => {
    const { user, logout } = useAuth();
    const [stats, setStats] = useState<DashboardStats>({
        totalElderly: 0,
        totalPreferences: 0,
        totalMedicalRecords: 0,
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        fetchDashboardData();
    }, []);

    const fetchDashboardData = async () => {
        try {
            // Fetch elderly profiles to get count
            const elderlyResponse = await axios.get('/elderly');
            const elderlyCount = elderlyResponse.data.length;

            // Calculate total preferences and medical records from all elderly
            let totalPreferences = 0;
            let totalMedicalRecords = 0;

            for (const elderly of elderlyResponse.data) {
                try {
                    const preferencesResponse = await axios.get(`/elderly/${elderly.id}/preferences`);
                    totalPreferences += preferencesResponse.data.length;

                    const medicalResponse = await axios.get(`/elderly/${elderly.id}/medical-summary`);
                    totalMedicalRecords += medicalResponse.data.recent_records.length;
                } catch (err) {
                    // Continue if individual requests fail
                    console.warn(`Failed to fetch data for elderly ${elderly.id}:`, err);
                }
            }

            setStats({
                totalElderly: elderlyCount,
                totalPreferences,
                totalMedicalRecords,
            });
        } catch (err) {
            setError('Failed to load dashboard data');
            console.error('Dashboard data fetch error:', err);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return <div className="loading">Loading dashboard...</div>;
    }

    return (
        <div className="dashboard">
            <div className="header">
                <h1>ElderComp Caregiver Dashboard</h1>
                <div className="user-info">
                    <span>Welcome, {user?.full_name}</span>
                    <button onClick={logout} className="logout-button">
                        Logout
                    </button>
                </div>
            </div>

            <div className="nav-links">
                <Link to="/dashboard" className="nav-link">Dashboard</Link>
                <Link to="/elderly" className="nav-link">Elderly Profiles</Link>
            </div>

            {error && <div className="error">{error}</div>}

            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-number">{stats.totalElderly}</div>
                    <div className="stat-label">Total Elderly Profiles</div>
                </div>
                <div className="stat-card">
                    <div className="stat-number">{stats.totalPreferences}</div>
                    <div className="stat-label">Personal Preferences</div>
                </div>
                <div className="stat-card">
                    <div className="stat-number">{stats.totalMedicalRecords}</div>
                    <div className="stat-label">Recent Medical Records</div>
                </div>
            </div>

            <div className="card">
                <h3>System Overview</h3>
                <p>
                    Welcome to the ElderComp Caregiver Interface. This system allows you to manage
                    elderly profiles, view their personal preferences, and access medical summaries
                    (non-sensitive data only).
                </p>
                <p>
                    <strong>Features:</strong>
                </p>
                <ul style={{ textAlign: 'left', maxWidth: '600px', margin: '0 auto' }}>
                    <li>View and manage elderly profiles</li>
                    <li>Access personal preferences and daily routines</li>
                    <li>View medical record summaries (encrypted data protected)</li>
                    <li>Add new personal preferences</li>
                    <li>Secure authentication with JWT tokens</li>
                </ul>
            </div>

            <div className="card">
                <h3>Quick Actions</h3>
                <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
                    <Link to="/elderly" className="nav-link">View All Elderly</Link>
                    <button
                        onClick={fetchDashboardData}
                        className="nav-link"
                        style={{ border: 'none', background: 'white', cursor: 'pointer' }}
                    >
                        Refresh Data
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
