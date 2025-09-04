import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

interface ElderlyProfile {
    id: string;
    first_name: string;
    last_name: string;
    preferred_name?: string;
    date_of_birth?: string;
    gender?: string;
    phone_number?: string;
    emergency_contact_name?: string;
    emergency_contact_phone?: string;
    address?: string;
}

const ElderlyList: React.FC = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [elderly, setElderly] = useState<ElderlyProfile[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        fetchElderlyProfiles();
    }, []);

    const fetchElderlyProfiles = async () => {
        try {
            const response = await axios.get('/elderly');
            setElderly(response.data);
        } catch (err) {
            setError('Failed to load elderly profiles');
            console.error('Elderly profiles fetch error:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleElderlyClick = (elderlyId: string) => {
        navigate(`/elderly/${elderlyId}`);
    };

    if (loading) {
        return <div className="loading">Loading elderly profiles...</div>;
    }

    return (
        <div className="dashboard">
            <div className="header">
                <h1>Elderly Profiles</h1>
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

            <div className="card">
                <h3>All Elderly Profiles ({elderly.length})</h3>
                <p>Click on any profile to view detailed information and preferences.</p>
            </div>

            <div className="elderly-grid">
                {elderly.map((person) => (
                    <div
                        key={person.id}
                        className="elderly-card"
                        onClick={() => handleElderlyClick(person.id)}
                    >
                        <div className="elderly-name">
                            {person.first_name} {person.last_name}
                            {person.preferred_name && (
                                <span style={{ fontSize: '0.9rem', color: '#666', fontWeight: 'normal' }}>
                                    {' '}({person.preferred_name})
                                </span>
                            )}
                        </div>

                        {person.date_of_birth && (
                            <div className="elderly-info">
                                <strong>Born:</strong> {new Date(person.date_of_birth).toLocaleDateString()}
                            </div>
                        )}

                        {person.gender && (
                            <div className="elderly-info">
                                <strong>Gender:</strong> {person.gender}
                            </div>
                        )}

                        {person.phone_number && (
                            <div className="elderly-info">
                                <strong>Phone:</strong> {person.phone_number}
                            </div>
                        )}

                        {person.emergency_contact_name && (
                            <div className="elderly-info">
                                <strong>Emergency Contact:</strong> {person.emergency_contact_name}
                                {person.emergency_contact_phone && (
                                    <span> ({person.emergency_contact_phone})</span>
                                )}
                            </div>
                        )}

                        {person.address && (
                            <div className="elderly-info">
                                <strong>Address:</strong> {person.address}
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {elderly.length === 0 && !loading && (
                <div className="card">
                    <h3>No Elderly Profiles Found</h3>
                    <p>There are currently no elderly profiles in the system.</p>
                </div>
            )}
        </div>
    );
};

export default ElderlyList;
