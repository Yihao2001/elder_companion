import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { BASE_URL } from '../config';

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
    ltm_id: string;
    category: string;
    key: string;
    value: string;
    last_updated: string;
}

interface HealthcareInfo {
    healthcare_id: string;
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
    // const db_auth = { headers: { Authorization: `Bearer ${AUTH_TOKEN}` }}

    useEffect(() => {
        const fetchProfile = async () => {
            try {
                const [elderlyRes, ltmRes, healthcareRes] = await Promise.all([
                    axios.get(`${BASE_URL}/elderly?elderly_id=${id}`),
                    axios.get(`${BASE_URL}/ltm?elderly_id=${id}`),
                    axios.get(`${BASE_URL}/healthcare?elderly_id=${id}`)
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

    const handleEditClick = () => {
        navigate(`/elderly/${id}/edit`);
    };

    if (loading) return <div>Loading profile...</div>;
    if (error) return <div>{error}</div>;
    if (!elderly) return <div>No profile found</div>;

    return (
        <div className="elderly-detail">
            <div className="content-wrapper">
                <div className="header">
                    <h1>Care Recipient Profiles</h1>
                    <div className="user-info">
                        <span>Welcome, {user?.username}</span>
                        <button onClick={logout} className="logout-button">
                            Logout
                        </button>
                    </div>
                </div>

                {/* Elderly Section */}
                <div className="section elderly-section">
                    <h2>{elderly.name}</h2>
                    <button onClick={handleEditClick} className="edit-button">
                        ✏️ Edit Records
                    </button>
                    <table>
                        <tbody>
                            {elderly.preferred_name && (
                                <tr>
                                    <td>Preferred Name</td>
                                    <td>{elderly.preferred_name}</td>
                                </tr>
                            )}
                            {elderly.date_of_birth && (
                                <tr>
                                    <td>Date of Birth</td>
                                    <td>{new Date(elderly.date_of_birth).toLocaleDateString()}</td>
                                </tr>
                            )}
                            {elderly.gender && (
                                <tr>
                                    <td>Gender</td>
                                    <td>{elderly.gender}</td>
                                </tr>
                            )}
                            {elderly.dialect_group && (
                                <tr>
                                    <td>Dialect Group</td>
                                    <td>{elderly.dialect_group}</td>
                                </tr>
                            )}
                            {elderly.marital_status && (
                                <tr>
                                    <td>Marital Status</td>
                                    <td>{elderly.marital_status}</td>
                                </tr>
                            )}
                            {elderly.nationality && (
                                <tr>
                                    <td>Nationality</td>
                                    <td>{elderly.nationality}</td>
                                </tr>
                            )}
                            {elderly.phone_number && (
                                <tr>
                                    <td>Phone</td>
                                    <td>{elderly.phone_number}</td>
                                </tr>
                            )}
                            {elderly.address && (
                                <tr>
                                    <td>Address</td>
                                    <td>{elderly.address}</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Healthcare Section */}
                {healthcareInfo.length > 0 && (
                    <div className="section healthcare-section">
                        <h3 className="section-header">Healthcare Records</h3>
                        <table>
                            <thead>
                                <tr>
                                    <th>Condition</th>
                                    <th></th>
                                    <th></th>
                                </tr>
                            </thead>
                            <tbody>
                                {healthcareInfo.map((record, index) => (
                                    <>
                                        <tr key={`main-${index}`}>
                                            <td rowSpan={3}>{record.description}</td>
                                            <td>Type</td>
                                            <td>{record.record_type}</td>
                                        </tr>
                                        <tr key={`diagnosis-${index}`}>
                                            <td>Diagnosed</td>
                                            <td>{new Date(record.diagnosis_date).toLocaleDateString()}</td>
                                        </tr>
                                        <tr key={`updated-${index}`}>
                                            <td>Last Updated</td>
                                            <td>{new Date(record.last_updated).toLocaleDateString()}</td>
                                        </tr>
                                    </>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* LTM Section */}
                {ltmInfo.length > 0 && (
                    <div className="section ltm-section">
                        <h3 className="section-header">Additional Information</h3>
                        <table>
                            <thead>
                                <tr>
                                    <th>Category</th>
                                    <th></th>
                                    <th></th>
                                </tr>
                            </thead>
                            <tbody>
                                {ltmInfo.map((item, idx) => (
                                    <tr key={idx}>
                                        <td>{item.category}</td>
                                        <td>{item.key.replace('_', ' ')}</td>
                                        <td>{item.value}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                <button onClick={() => navigate(-1)} className="back-button">
                    ← Back
                </button>
            </div>
        </div>

    );
};

export default ElderlyDetail;
