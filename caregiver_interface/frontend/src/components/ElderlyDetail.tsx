import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

interface ElderlyProfile {
    id: string;
    name: string;
    preferred_name?: string;
    date_of_birth?: string;
    gender?: string;
    phone_number?: string;
    address?: string;
    marital_status?: string;
    dialect_group?: string;
    nationality?: string;
}

interface LTMInfo {
    category: string;
    key: string;
    value: string;
    last_updated: string;
}

interface HealthcareInfo {
    description: string;
    diagnosis_date: string;
    last_updated: string;
    record_type: string;
}

const ElderlyDetail: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const [elderly, setElderly] = useState<ElderlyProfile | null>(null);
    const [ltmInfo, setLtmInfo] = useState<LTMInfo[]>([]);
    const [healthcareInfo, setHealthcareInfo] = useState<HealthcareInfo[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchProfile = async () => {
            try {
                const [elderlyRes, ltmRes, healthcareRes] = await Promise.all([
                    axios.get(
                        `http://127.0.0.1:5000/api/elderly?elderly_id=${id}`,
                        {
                            headers: {
                                Authorization: `Bearer 3cb6ec9cca42a2924cc3a592418006afa6b3487eeff92e3b714a5a004de3f033`
                            }
                        }
                    ),
                    axios.get(
                        `http://127.0.0.1:5000/api/ltm?elderly_id=${id}`,
                        {
                            headers: {
                                Authorization: `Bearer 3cb6ec9cca42a2924cc3a592418006afa6b3487eeff92e3b714a5a004de3f033`
                            }
                        }
                    ),
                    axios.get(
                        `http://127.0.0.1:5000/api/healthcare?elderly_id=${id}`,
                        {
                            headers: {
                                Authorization: `Bearer 3cb6ec9cca42a2924cc3a592418006afa6b3487eeff92e3b714a5a004de3f033`
                            }
                        }
                    )
                ]);

                setElderly(elderlyRes.data);
                setLtmInfo(ltmRes.data);
                setHealthcareInfo(healthcareRes.data);
            } catch (err) {
                setError('Failed to load elderly details');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchProfile();
    }, [id]);

    if (loading) return <div>Loading profile...</div>;
    if (error) return <div>{error}</div>;
    if (!elderly) return <div>No profile found</div>;

    return (
        <div className="elderly-detail">
            <div className="header">
                <h1>Elderly Profiles</h1>
                <div className="user-info">
                    <span>Welcome, {user?.full_name}</span>
                    <button onClick={logout} className="logout-button">
                        Logout
                    </button>
                </div>
            </div>

            <h2>{elderly.name}</h2>
            {elderly.preferred_name && (
                <p><strong>Preferred Name:</strong> {elderly.preferred_name}</p>
            )}
            {elderly.date_of_birth && (
                <p><strong>Date of Birth:</strong> {new Date(elderly.date_of_birth).toLocaleDateString()}</p>
            )}
            {elderly.gender && <p><strong>Gender:</strong> {elderly.gender}</p>}
            {elderly.dialect_group && <p><strong>Dialect Group:</strong> {elderly.dialect_group}</p>}
            {elderly.marital_status && <p><strong>Marital Status:</strong> {elderly.marital_status}</p>}
            {elderly.nationality && <p><strong>Nationality:</strong> {elderly.nationality}</p>}
            {elderly.phone_number && <p><strong>Phone:</strong> {elderly.phone_number}</p>}
            {elderly.address && <p><strong>Address:</strong> {elderly.address}</p>}

            {/* Healthcare Info Section */}
            {healthcareInfo.length > 0 && (
                <div className="healthcare-section">
                    <h3>Healthcare Records</h3>
                    <ul>
                        {healthcareInfo.map((record, index) => (
                            <li key={index}>
                                <strong>{record.description}</strong> ({record.record_type})<br />
                                Diagnosed: {new Date(record.diagnosis_date).toLocaleDateString()}<br />
                                <small><em>Last updated: {new Date(record.last_updated).toLocaleDateString()}</em></small>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {/* Extra LTM Info Section */}
            {ltmInfo.length > 0 && (
                <div className="ltm-section">
                    <h3>Additional Information</h3>
                    <ul>
                        {ltmInfo.map((item, idx) => (
                            <li key={idx}>
                                <strong>{item.key.replace('_', ' ')}:</strong> {item.value} <br />
                                <small><em>(Category: {item.category}, Last updated: {new Date(item.last_updated).toLocaleDateString()})</em></small>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
            <button onClick={() => navigate(-1)} className="back-button">
                ← Back
            </button>
        </div>
    );
};

export default ElderlyDetail;
