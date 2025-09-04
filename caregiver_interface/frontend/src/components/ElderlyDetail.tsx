import React, { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
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

interface PersonalPreference {
    id: string;
    elderly_id: string;
    category: string;
    preference_name: string;
    preference_value?: string;
    importance_level: number;
    notes?: string;
}

interface MedicalSummary {
    elderly_id: string;
    recent_records: Array<{
        type: string;
        title: string;
        date: string;
        provider: string;
    }>;
    summary: {
        active_medications: number;
        active_conditions: number;
        known_allergies: number;
    };
}

const ElderlyDetail: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const { user, logout } = useAuth();
    const [profile, setProfile] = useState<ElderlyProfile | null>(null);
    const [preferences, setPreferences] = useState<PersonalPreference[]>([]);
    const [medicalSummary, setMedicalSummary] = useState<MedicalSummary | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        if (id) {
            fetchElderlyData(id);
        }
    }, [id]);

    const fetchElderlyData = async (elderlyId: string) => {
        try {
            // Fetch profile
            const profileResponse = await axios.get(`/elderly/${elderlyId}`);
            setProfile(profileResponse.data);

            // Fetch preferences
            const preferencesResponse = await axios.get(`/elderly/${elderlyId}/preferences`);
            setPreferences(preferencesResponse.data);

            // Fetch medical summary
            const medicalResponse = await axios.get(`/elderly/${elderlyId}/medical-summary`);
            setMedicalSummary(medicalResponse.data);

        } catch (err) {
            setError('Failed to load elderly data');
            console.error('Elderly data fetch error:', err);
        } finally {
            setLoading(false);
        }
    };

    const groupPreferencesByCategory = (prefs: PersonalPreference[]) => {
        return prefs.reduce((groups, pref) => {
            const category = pref.category;
            if (!groups[category]) {
                groups[category] = [];
            }
            groups[category].push(pref);
            return groups;
        }, {} as Record<string, PersonalPreference[]>);
    };

    if (loading) {
        return <div className="loading">Loading elderly details...</div>;
    }

    if (!profile) {
        return (
            <div className="dashboard">
                <div className="error">Elderly profile not found</div>
                <Link to="/elderly" className="nav-link">Back to Elderly List</Link>
            </div>
        );
    }

    const groupedPreferences = groupPreferencesByCategory(preferences);

    return (
        <div className="dashboard">
            <div className="header">
                <h1>Elderly Profile Details</h1>
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

            {/* Profile Information */}
            <div className="card">
                <h3>
                    {profile.first_name} {profile.last_name}
                    {profile.preferred_name && (
                        <span style={{ fontSize: '0.9rem', color: '#666', fontWeight: 'normal' }}>
                            {' '}({profile.preferred_name})
                        </span>
                    )}
                </h3>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem', textAlign: 'left' }}>
                    {profile.date_of_birth && (
                        <div>
                            <strong>Date of Birth:</strong><br />
                            {new Date(profile.date_of_birth).toLocaleDateString()}
                        </div>
                    )}

                    {profile.gender && (
                        <div>
                            <strong>Gender:</strong><br />
                            {profile.gender}
                        </div>
                    )}

                    {profile.phone_number && (
                        <div>
                            <strong>Phone Number:</strong><br />
                            {profile.phone_number}
                        </div>
                    )}

                    {profile.emergency_contact_name && (
                        <div>
                            <strong>Emergency Contact:</strong><br />
                            {profile.emergency_contact_name}
                            {profile.emergency_contact_phone && (
                                <><br />{profile.emergency_contact_phone}</>
                            )}
                        </div>
                    )}

                    {profile.address && (
                        <div>
                            <strong>Address:</strong><br />
                            {profile.address}
                        </div>
                    )}
                </div>
            </div>

            {/* Medical Summary */}
            {medicalSummary && (
                <div className="card">
                    <h3>Medical Summary</h3>
                    <div className="stats-grid">
                        <div className="stat-card">
                            <div className="stat-number">{medicalSummary.summary.active_medications}</div>
                            <div className="stat-label">Active Medications</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-number">{medicalSummary.summary.active_conditions}</div>
                            <div className="stat-label">Active Conditions</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-number">{medicalSummary.summary.known_allergies}</div>
                            <div className="stat-label">Known Allergies</div>
                        </div>
                    </div>

                    {medicalSummary.recent_records.length > 0 && (
                        <div style={{ marginTop: '1rem' }}>
                            <h4>Recent Medical Records</h4>
                            <div style={{ display: 'grid', gap: '0.5rem' }}>
                                {medicalSummary.recent_records.map((record, index) => (
                                    <div key={index} style={{
                                        padding: '0.75rem',
                                        background: '#f8f9fa',
                                        borderRadius: '5px',
                                        textAlign: 'left'
                                    }}>
                                        <strong>{record.title}</strong> ({record.type})
                                        <br />
                                        <small>
                                            {new Date(record.date).toLocaleDateString()} - {record.provider}
                                        </small>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Personal Preferences */}
            <div className="card">
                <h3>Personal Preferences ({preferences.length})</h3>

                {Object.keys(groupedPreferences).length > 0 ? (
                    Object.entries(groupedPreferences).map(([category, prefs]) => (
                        <div key={category} style={{ marginBottom: '1.5rem' }}>
                            <h4 style={{
                                textTransform: 'capitalize',
                                color: '#667eea',
                                borderBottom: '2px solid #667eea',
                                paddingBottom: '0.5rem'
                            }}>
                                {category} ({prefs.length})
                            </h4>
                            <div style={{ display: 'grid', gap: '0.75rem', marginTop: '1rem' }}>
                                {prefs.map((pref) => (
                                    <div key={pref.id} style={{
                                        padding: '1rem',
                                        background: '#f8f9fa',
                                        borderRadius: '5px',
                                        textAlign: 'left'
                                    }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                            <strong>{pref.preference_name}</strong>
                                            <span style={{
                                                background: '#667eea',
                                                color: 'white',
                                                padding: '0.25rem 0.5rem',
                                                borderRadius: '3px',
                                                fontSize: '0.8rem'
                                            }}>
                                                Importance: {pref.importance_level}/10
                                            </span>
                                        </div>
                                        {pref.preference_value && (
                                            <div style={{ margin: '0.5rem 0', color: '#333' }}>
                                                {pref.preference_value}
                                            </div>
                                        )}
                                        {pref.notes && (
                                            <div style={{ fontSize: '0.9rem', color: '#666', fontStyle: 'italic' }}>
                                                Note: {pref.notes}
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))
                ) : (
                    <p>No personal preferences recorded for this person.</p>
                )}
            </div>
        </div>
    );
};

export default ElderlyDetail;
