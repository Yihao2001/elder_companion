import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { BASE_URL } from '../config';

interface LTMInfo {
    ltm_id: string;
    category: string;
    key: string;
    value: string;
    last_updated: string;
}

interface HealthcareInfo {
    healthcare_record_id: string;
    description: string;
    diagnosis_date: string;
    last_updated: string;
    record_type: string;
}

const LTM_CATEGORIES = [
  "personal",
  "family",
  "education",
  "career",
  "lifestyle",
  "finance",
  "legal"
] as const;

const RECORD_TYPES = [
  "condition",
  "procedure",
  "appointment",
  "medication"
] as const;


const ElderlyEdit: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const [selectedSection, setSelectedSection] = useState<'ltm' | 'healthcare'>('healthcare');
    const [mode, setMode] = useState<'edit' | 'create'>('edit');
    const [ltmInfo, setLtmInfo] = useState<LTMInfo[]>([]);
    const [healthcareInfo, setHealthcareInfo] = useState<HealthcareInfo[]>([]);
    const [selectedRecord, setSelectedRecord] = useState<LTMInfo | HealthcareInfo | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    // const db_auth = { headers: { Authorization: `Bearer ${AUTH_TOKEN}` }};

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [ltmRes, healthcareRes] = await Promise.all([
                    axios.get(`${BASE_URL}/ltm?elderly_id=${id}`),
                    axios.get(`${BASE_URL}/healthcare?elderly_id=${id}`)
                ]);
                setLtmInfo(ltmRes.data);
                setHealthcareInfo(healthcareRes.data);
                console.log("LTM data:", ltmRes.data);
                console.log("Healthcare data:", healthcareRes.data);
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

        console.log("Selected record:", selectedRecord);

        setSaving(true);
        setError('');
        setSuccess('');

        try {
            if (selectedSection === 'ltm') {
                const ltmRecord = selectedRecord as LTMInfo;

                if (mode === 'create') {
                    // CREATE uses POST
                    await axios.post(`${BASE_URL}/ltm`, {
                        elderly_id: id,
                        category: ltmRecord.category,
                        key: ltmRecord.key,
                        value: ltmRecord.value
                    });
                } else {
                    // EDIT uses PUT
                    await axios.put(
                        `${BASE_URL}/ltm?ltm_id=${ltmRecord.ltm_id}`,
                        {
                            category: ltmRecord.category,
                            key: ltmRecord.key,
                            value: ltmRecord.value
                        }
                    );
                }

                // Update local state
                setLtmInfo(prev => prev.map(item => 
                    item.ltm_id === ltmRecord.ltm_id
                        ? { ...ltmRecord, last_updated: new Date().toISOString() }
                        : item
                ));
            } else {
                const healthRecord = selectedRecord as HealthcareInfo;

                if (mode === 'create') {
                    // CREATE uses POST
                    await axios.post(`${BASE_URL}/healthcare`, {
                        elderly_id: id,
                        description: healthRecord.description,
                        diagnosis_date: healthRecord.diagnosis_date,
                        record_type: healthRecord.record_type
                    });
                } else {
                    // EDIT uses PUT
                    await axios.put(
                        `${BASE_URL}/healthcare?healthcare_record_id=${healthRecord.healthcare_record_id}`, 
                        {
                            description: healthRecord.description,
                            diagnosis_date: healthRecord.diagnosis_date,
                            record_type: healthRecord.record_type
                        }
                    );
                }

                // Update local state
                setHealthcareInfo(prev => prev.map(item => 
                    item.healthcare_record_id === healthRecord.healthcare_record_id
                        ? { ...healthRecord, last_updated: new Date().toISOString() }
                        : item
                ));
            }

            setSuccess(mode === 'create' ? 'Record created successfully!' : 'Record updated successfully!');
        } catch (err) {
            setError(mode === 'create' ? 'Failed to create record' : 'Failed to update record');
            console.error(err);
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div>Loading records...</div>;

    const currentRecords = selectedSection === 'healthcare' ? healthcareInfo : ltmInfo;

    return (
        <div className="elderly-edit">
            <div className="edit-container">
                <div className="header">
                    <h1>Edit Care Recipient Records</h1>
                    <div className="user-info">
                        <span>Welcome, {user?.username}</span>
                        <button onClick={logout} className="logout-button">
                            Logout
                        </button>
                    </div>
                </div>

                {/* Section Selection Dropdown */}
                <div className="section-selector">
                    <label htmlFor="section-select"><strong>Information Type:</strong></label>
                    <select 
                        id="section-select"
                        value={selectedSection} 
                        onChange={(e) => handleSectionChange(e.target.value as 'healthcare' | 'ltm')}
                        className="section-dropdown"
                    >
                        <option value="healthcare">Healthcare Records</option>
                        <option value="ltm">Long Term Memory (LTM)</option>
                    </select>
                </div>

                {/* Mode Selection Dropdown */}
                <div className="mode-selector">
                    <label htmlFor="mode-select"><strong>Action:</strong></label>
                    <select
                        id="mode-select"
                        value={mode}
                        onChange={(e) => {
                        const newMode = e.target.value as 'edit' | 'create';
                        setMode(newMode);
                        if (newMode === 'create') {
                            const newRecord = selectedSection === 'ltm'
                                ? { category: '', key: '', value: '', last_updated: '' }
                                : { description: '', diagnosis_date: '', record_type: '', last_updated: '' };
                            setSelectedRecord(newRecord as LTMInfo | HealthcareInfo);
                        } else {
                            setSelectedRecord(null);
                        }                        }}
                        className="mode-dropdown"
                    >
                        <option value="edit">Edit Existing Record</option>
                        <option value="create">Create New Record</option>
                    </select>
                </div>

                {/* Record Selection Dropdown */}
                {mode === 'edit' && currentRecords.length > 0 && (
                    <div className="record-selector">
                        <label htmlFor="record-select"><strong>
                            {selectedSection === 'ltm' ? 'Select Category:' : 'Select Description:'}
                        </strong></label>
                        <select
                            id="record-select"
                            className="record-dropdown"
                            onChange={(e) => {
                                const value = e.target.value;

                                if (selectedSection === "ltm") {
                                    const records = currentRecords as LTMInfo[];
                                    const record = records.find((r: LTMInfo) => r.category === value);
                                    setSelectedRecord(record || null);
                                } else {
                                    const records = currentRecords as HealthcareInfo[];
                                    const record = records.find((r: HealthcareInfo) => r.description === value);
                                    setSelectedRecord(record || null);
                                }
                            }}

                        >
                            <option value="">-- Choose --</option>
                            {currentRecords.map((record, index) => (
                                <option 
                                    key={index} 
                                    value={selectedSection === 'ltm' 
                                        ? (record as LTMInfo).category 
                                        : (record as HealthcareInfo).description}
                                >
                                    {selectedSection === 'ltm' 
                                        ? (record as LTMInfo).category 
                                        : (record as HealthcareInfo).description}
                                </option>
                            ))}
                        </select>
                    </div>
                )}

                {/* Create Form in Table Format */}
                {mode === 'create' && (
                    <div className="create-form">
                        <h3>Create {selectedSection === 'ltm' ? 'LTM' : 'Healthcare'} Record</h3>
                        <table className="create-table">
                            <tbody>
                                {selectedSection === 'ltm' ? (
                                    <>
                                        <tr>
                                            <td><strong>Category</strong></td>
                                            <td>
                                                <select onChange={(e) => handleFieldChange('category', e.target.value)}>
                                                    <option value="">-- Select Category --</option>
                                                    {LTM_CATEGORIES.map((cat) => (
                                                        <option key={cat} value={cat}>{cat}</option>
                                                    ))}
                                                </select>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td><strong>Key</strong></td>
                                            <td>
                                                <input 
                                                    type="text" 
                                                    onChange={(e) => handleFieldChange('key', e.target.value)}
                                                />
                                            </td>
                                        </tr>
                                        <tr>
                                            <td><strong>Value</strong></td>
                                            <td>
                                                <textarea
                                                    rows={3}
                                                    onChange={(e) => handleFieldChange('value', e.target.value)}
                                                />
                                            </td>
                                        </tr>
                                    </>
                                ) : (
                                    <>
                                        <tr>
                                            <td><strong>Description</strong></td>
                                            <td>
                                                <textarea
                                                    rows={3}
                                                    onChange={(e) => handleFieldChange('description', e.target.value)}
                                                />
                                            </td>
                                        </tr>
                                        <tr>
                                            <td><strong>Record Type</strong></td>
                                            <td>
                                                <select onChange={(e) => handleFieldChange('record_type', e.target.value)}>
                                                    <option value="">-- Select Record Type --</option>
                                                    {RECORD_TYPES.map((type) => (
                                                        <option key={type} value={type}>{type}</option>
                                                    ))}
                                                </select>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td><strong>Diagnosis Date</strong></td>
                                            <td>
                                                <input 
                                                    type="date" 
                                                    onChange={(e) => handleFieldChange('diagnosis_date', e.target.value)}
                                                />
                                            </td>
                                        </tr>
                                    </>
                                )}
                            </tbody>
                        </table>

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

                {/* Edit Form in Table Format */}
                {mode === 'edit' && selectedRecord && (
                    <div className="edit-form">
                        <h3>Edit {selectedSection === 'ltm' ? 'LTM' : 'Healthcare'} Record</h3>
                        <table className="edit-table">
                            <tbody>
                                {selectedSection === 'ltm' ? (
                                    <>
                                        <tr>
                                            <td><strong>Category</strong></td>
                                            <td>
                                                <select
                                                value={(selectedRecord as LTMInfo).category}
                                                onChange={(e) => handleFieldChange('category', e.target.value)}
                                                >
                                                <option value="">-- Select Category --</option>
                                                {LTM_CATEGORIES.map((cat) => (
                                                    <option key={cat} value={cat}>{cat}</option>
                                                ))}
                                                </select>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td><strong>Key</strong></td>
                                            <td>
                                                <input 
                                                    type="text" 
                                                    value={(selectedRecord as LTMInfo).key}
                                                    onChange={(e) => handleFieldChange('key', e.target.value)}
                                                />
                                            </td>
                                        </tr>
                                        <tr>
                                            <td><strong>Value</strong></td>
                                            <td>
                                                <textarea
                                                    rows={3}
                                                    value={(selectedRecord as LTMInfo).value}
                                                    onChange={(e) => handleFieldChange('value', e.target.value)}
                                                />
                                            </td>
                                        </tr>
                                    </>
                                ) : (
                                    <>
                                        <tr>
                                            <td><strong>Description</strong></td>
                                            <td>
                                                <textarea
                                                    rows={3}
                                                    value={(selectedRecord as HealthcareInfo).description}
                                                    onChange={(e) => handleFieldChange('description', e.target.value)}
                                                />
                                            </td>
                                        </tr>
                                        <tr>
                                            <td><strong>Record Type</strong></td>
                                            <td>
                                                <select
                                                value={(selectedRecord as HealthcareInfo).record_type}
                                                onChange={(e) => handleFieldChange('record_type', e.target.value)}
                                                >
                                                <option value="">-- Select Record Type --</option>
                                                {RECORD_TYPES.map((type) => (
                                                    <option key={type} value={type}>{type}</option>
                                                ))}
                                                </select>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td><strong>Diagnosis Date</strong></td>
                                            <td>
                                                <input 
                                                    type="date" 
                                                    value={(selectedRecord as HealthcareInfo).diagnosis_date 
                                                        ? new Date((selectedRecord as HealthcareInfo).diagnosis_date).toISOString().split('T')[0] 
                                                        : ''}
                                                    onChange={(e) => handleFieldChange('diagnosis_date', e.target.value)}
                                                />
                                            </td>
                                        </tr>
                                    </>
                                )}
                            </tbody>
                        </table>

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