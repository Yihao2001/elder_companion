import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

interface LTMInfo {
    id?: string;
    category: string;
    key: string;
    value: string;
    last_updated: string;
}

interface HealthcareInfo {
    id?: string;
    description: string;
    diagnosis_date: string;
    last_updated: string;
    record_type: string;
}

const ElderlyEdit: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const [selectedSection, setSelectedSection] = useState<'ltm' | 'healthcare'>('ltm');
    const [ltmInfo, setLtmInfo] = useState<LTMInfo[]>([]);
    const [healthcareInfo, setHealthcareInfo] = useState<HealthcareInfo[]>([]);
    const [selectedRecord, setSelectedRecord] = useState<LTMInfo | HealthcareInfo | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const db_auth = { headers: { Authorization: `Bearer TOKEN` }};

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [ltmRes, healthcareRes] = await Promise.all([
                    axios.get(`http://127.0.0.1:5000/api/ltm?elderly_id=${id}`, db_auth),
                    axios.get(`http://127.0.0.1:5000/api/healthcare?elderly_id=${id}`, db_auth)
                ]);
                setLtmInfo(ltmRes.data);
                setHealthcareInfo(healthcareRes.data);
            } catch (err) {
                setError('Failed to load records');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [id]);

    const handleSectionChange = (section: 'ltm' | 'healthcare') => {
        setSelectedSection(section);
        setSelectedRecord(null);
        setError('');
        setSuccess('');
    };

    const handleRecordSelect = (record: LTMInfo | HealthcareInfo) => {
        setSelectedRecord(record);
        setError('');
        setSuccess('');
    };

    const handleFieldChange = (field: string, value: string) => {
        if (selectedRecord) {
            setSelectedRecord({
                ...selectedRecord,
                [field]: value
            });
        }
    };

    const handleSave = async () => {
        if (!selectedRecord) return;

        setSaving(true);
        setError('');
        setSuccess('');

        try {
            if (selectedSection === 'ltm') {
                const ltmRecord = selectedRecord as LTMInfo;
                await axios.post('http://127.0.0.1:5000/api/ltm', {
                    elderly_id: id,
                    category: ltmRecord.category,
                    key: ltmRecord.key,
                    value: ltmRecord.value
                }, db_auth);
                
                // Update local state
                setLtmInfo(prev => prev.map(item => 
                    item.key === ltmRecord.key && item.category === ltmRecord.category 
                        ? { ...ltmRecord, last_updated: new Date().toISOString() }
                        : item
                ));
            } else {
                const healthRecord = selectedRecord as HealthcareInfo;
                await axios.post('http://127.0.0.1:5000/api/healthcare', {
                    elderly_id: id,
                    description: healthRecord.description,
                    diagnosis_date: healthRecord.diagnosis_date,
                    record_type: healthRecord.record_type
                }, db_auth);
                
                // Update local state
                setHealthcareInfo(prev => prev.map(item => 
                    item.description === healthRecord.description && item.record_type === healthRecord.record_type
                        ? { ...healthRecord, last_updated: new Date().toISOString() }
                        : item
                ));
            }
            
            setSuccess('Record updated successfully!');
        } catch (err) {
            setError('Failed to update record');
            console.error(err);
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div>Loading records...</div>;

    const currentRecords = selectedSection === 'ltm' ? ltmInfo : healthcareInfo;

    return (
        <div className="elderly-edit">
            <div className="header">
                <h1>Edit Elderly Records</h1>
                <div className="user-info">
                    <span>Welcome, {user?.full_name}</span>
                    <button onClick={logout} className="logout-button">
                        Logout
                    </button>
                </div>
            </div>

            <div className="edit-container">
                {/* Section Selection Dropdown */}
                <div className="section-selector">
                    <label htmlFor="section-select"><strong>Select Section to Edit:</strong></label>
                    <select 
                        id="section-select"
                        value={selectedSection} 
                        onChange={(e) => handleSectionChange(e.target.value as 'ltm' | 'healthcare')}
                        className="section-dropdown"
                    >
                        <option value="ltm">Long Term Memory (LTM)</option>
                        <option value="healthcare">Healthcare Records</option>
                    </select>
                </div>

                {/* Record Selection */}
                {currentRecords.length > 0 && (
                    <div className="record-selector">
                        <label><strong>Select Record to Edit:</strong></label>
                        <div className="records-list">
                            {currentRecords.map((record, index) => (
                                <div 
                                    key={index} 
                                    className={`record-item ${selectedRecord === record ? 'selected' : ''}`}
                                    onClick={() => handleRecordSelect(record)}
                                >
                                    {selectedSection === 'ltm' ? (
                                        <span>{(record as LTMInfo).key.replace('_', ' ')}: {(record as LTMInfo).value}</span>
                                    ) : (
                                        <span>{(record as HealthcareInfo).description} ({(record as HealthcareInfo).record_type})</span>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Edit Form */}
                {selectedRecord && (
                    <div className="edit-form">
                        <h3>Edit {selectedSection === 'ltm' ? 'LTM' : 'Healthcare'} Record</h3>
                        
                        {selectedSection === 'ltm' ? (
                            <div className="ltm-form">
                                <div className="form-group">
                                    <label><strong>Category:</strong></label>
                                    <input 
                                        type="text" 
                                        value={(selectedRecord as LTMInfo).category}
                                        onChange={(e) => handleFieldChange('category', e.target.value)}
                                        className="form-input"
                                    />
                                </div>
                                <div className="form-group">
                                    <label><strong>Key:</strong></label>
                                    <input 
                                        type="text" 
                                        value={(selectedRecord as LTMInfo).key}
                                        onChange={(e) => handleFieldChange('key', e.target.value)}
                                        className="form-input"
                                    />
                                </div>
                                <div className="form-group">
                                    <label><strong>Value:</strong></label>
                                    <textarea 
                                        value={(selectedRecord as LTMInfo).value}
                                        onChange={(e) => handleFieldChange('value', e.target.value)}
                                        className="form-textarea"
                                        rows={4}
                                    />
                                </div>
                            </div>
                        ) : (
                            <div className="healthcare-form">
                                <div className="form-group">
                                    <label><strong>Description:</strong></label>
                                    <textarea 
                                        value={(selectedRecord as HealthcareInfo).description}
                                        onChange={(e) => handleFieldChange('description', e.target.value)}
                                        className="form-textarea"
                                        rows={3}
                                    />
                                </div>
                                <div className="form-group">
                                    <label><strong>Record Type:</strong></label>
                                    <input 
                                        type="text" 
                                        value={(selectedRecord as HealthcareInfo).record_type}
                                        onChange={(e) => handleFieldChange('record_type', e.target.value)}
                                        className="form-input"
                                    />
                                </div>
                                <div className="form-group">
                                    <label><strong>Diagnosis Date:</strong></label>
                                    <input 
                                        type="date" 
                                        value={(selectedRecord as HealthcareInfo).diagnosis_date ? new Date((selectedRecord as HealthcareInfo).diagnosis_date).toISOString().split('T')[0] : ''}
                                        onChange={(e) => handleFieldChange('diagnosis_date', e.target.value)}
                                        className="form-input"
                                    />
                                </div>
                            </div>
                        )}

                        {/* Status Messages */}
                        {error && <div className="error-message">{error}</div>}
                        {success && <div className="success-message">{success}</div>}

                        {/* Action Buttons */}
                        <div className="form-actions">
                            <button 
                                onClick={handleSave} 
                                disabled={saving}
                                className="save-button"
                            >
                                {saving ? 'Saving...' : 'Save Changes'}
                            </button>
                        </div>
                    </div>
                )}

                {currentRecords.length === 0 && (
                    <div className="no-records">
                        No {selectedSection === 'ltm' ? 'LTM' : 'healthcare'} records found.
                    </div>
                )}
            </div>

            <div className="navigation">
                <button onClick={() => navigate(-1)} className="back-button">
                    ← Back to Profile
                </button>
            </div>
        </div>
    );
};

export default ElderlyEdit;