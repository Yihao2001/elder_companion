import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

interface ElderlyProfile {
    id: string;
    name: string;
    preferred_name: string;
    date_of_birth?: string;
    gender?: string;
    phone_number?: string;
    address?: string;
    marital_status?: string;
    dialect_group?: string;
    nationality?: string;
}

const ElderlyList: React.FC = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [elderly, setElderly] = useState<ElderlyProfile[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [expandedId, setExpandedId] = useState<string | null>(null);


    useEffect(() => {
    // Temporary hardcoded list of elderly IDs you want to fetch
    const elderlyIds = ['1632319b-05ba-4ff9-ba35-be63a24e42af', '1632319b-05ba-4ff9-ba35-be63a24e42af'];

    const fetchProfiles = async () => {
        try {
            const results = await Promise.all(
                elderlyIds.map(id =>
                    axios.get(`http://127.0.0.1:5000/api/elderly?elderly_id=${id}`, {
                    headers: {
                        Authorization: `Bearer 3cb6ec9cca42a2924cc3a592418006afa6b3487eeff92e3b714a5a004de3f033`
                    }
                    }).then(res => res.data)
                )
            );
            setElderly(results);
        } catch (err) {
            setError("Failed to load elderly profiles");
            console.error("Elderly profiles fetch error:", err);
        } finally {
            setLoading(false);
        }};

        fetchProfiles();
    }, []);

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
                {/* <Link to="/dashboard" className="nav-link">Dashboard</Link> */}
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
                            {person.name}
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
