import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { BASE_URL } from '../config';

interface STMRecord {
    content: string;
    created_at: string;
}

interface ElderlySTMData {
    elderly_id: string;
    elderly_name: string;
    total_records: number;
    summary: string;
    key_points: string[];
}

interface DashboardData {
    date_range: {
        start: string;
        end: string;
    };
    elderly_summaries: ElderlySTMData[];
    last_generated: string;
}

const Dashboard: React.FC = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [selectedElderly, setSelectedElderly] = useState<string[]>([]);
    const [dateRange, setDateRange] = useState({
        start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        end: new Date().toISOString().split('T')[0]
    });

    const elderlyIds = ['1632319b-05ba-4ff9-ba35-be63a24e42af', '87654321-4321-4321-4321-019876543210'];

    const fetchDashboardData = async (startDate: string, endDate: string, idsToFetch?: string[]) => {
        try {
            setLoading(true);
            const summaries: ElderlySTMData[] = [];

            // Use selected elderly or all elderly if none selected
            const idsToUse = idsToFetch && idsToFetch.length > 0 ? idsToFetch : elderlyIds;

            // Fetch STM records for each elderly in the list
            for (const elderlyId of idsToUse) {
                try {
                    const stmResponse = await axios.get(`${BASE_URL}/stm`, {
                        params: {
                            elderly_id: elderlyId,
                            created_at_start: startDate,
                            created_at_end: endDate
                        }
                    });

                    const records: STMRecord[] = stmResponse.data;
                    const summary = generateSummary(records, elderlyId, startDate, endDate);
                    summaries.push(summary);
                } catch (err) {
                    console.error(`Failed to fetch STM for elderly ${elderlyId}:`, err);
                }
            }

            setDashboardData({
                date_range: { start: startDate, end: endDate },
                elderly_summaries: summaries,
                last_generated: new Date().toISOString()
            });
        } catch (err) {
            setError('Failed to load dashboard data');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const generateSummary = (records: STMRecord[], elderlyId: string, startDate: string, endDate: string): ElderlySTMData => {
        const keyPoints: Set<string> = new Set();

        records.forEach(record => {
            const sentences = record.content.split(/[.!?]+/);
            sentences.forEach(sentence => {
                const trimmed = sentence.trim();
                if (trimmed.length > 10) {
                    keyPoints.add(trimmed);
                }
            });
        });

        const topKeyPoints = Array.from(keyPoints).slice(0, 5);

        const summaryText = records.length > 0
            ? `Based on ${records.length} short-term memory records from ${startDate} to ${endDate}, this profile contains observations and notes about the care recipient's recent activities, behaviors, and interactions.`
            : 'No records found for this period.';

        return {
            elderly_id: elderlyId,
            elderly_name: `Care Recipient ${elderlyId.substring(0, 8)}`,
            total_records: records.length,
            summary: summaryText,
            key_points: topKeyPoints
        };
    };

    useEffect(() => {
        fetchDashboardData(dateRange.start, dateRange.end);
    }, []);

    const handleDateChange = (type: 'start' | 'end', value: string) => {
        const newRange = { ...dateRange, [type]: value };
        setDateRange(newRange);
        fetchDashboardData(newRange.start, newRange.end, selectedElderly);
    };

    const handleRefresh = () => {
        fetchDashboardData(dateRange.start, dateRange.end, selectedElderly);
    };

    const handleElderlyToggle = (elderlyId: string) => {
        const updated = selectedElderly.includes(elderlyId)
            ? selectedElderly.filter(id => id !== elderlyId)
            : [...selectedElderly, elderlyId];
        setSelectedElderly(updated);
        fetchDashboardData(dateRange.start, dateRange.end, updated);
    };

    const handleSelectAll = () => {
        if (selectedElderly.length === elderlyIds.length) {
            setSelectedElderly([]);
        } else {
            setSelectedElderly([...elderlyIds]);
            fetchDashboardData(dateRange.start, dateRange.end, elderlyIds);
        }
    };

    if (loading) return <div>Loading dashboard...</div>;
    if (error) return <div>{error}</div>;

    return (
        <div className="dashboard">
            <div className="content-wrapper">
                <div className="header">
                    <h1>Care Recipients Dashboard</h1>
                    <div className="user-info">
                        <span>Welcome, {user?.username}</span>
                        <button onClick={logout} className="logout-button">
                            Logout
                        </button>
                    </div>
                </div>

                {/* Date Range Filter */}
                <div className="section filter-section">
                    <h3>Filter by Date Range</h3>
                    <div className="date-filter">
                        <div className="date-input-group">
                            <label>From:</label>
                            <input
                                type="date"
                                value={dateRange.start}
                                onChange={(e) => handleDateChange('start', e.target.value)}
                            />
                        </div>
                        <div className="date-input-group">
                            <label>To:</label>
                            <input
                                type="date"
                                value={dateRange.end}
                                onChange={(e) => handleDateChange('end', e.target.value)}
                            />
                        </div>
                        <button onClick={handleRefresh} className="refresh-button">
                            🔄 Refresh
                        </button>
                    </div>
                </div>

                {/* Elderly Summaries */}
                {dashboardData && dashboardData.elderly_summaries.length > 0 ? (
                    <div className="section summaries-section">
                        <h2>Care Recipients Summary</h2>
                        <div className="summary-grid">
                            {dashboardData.elderly_summaries.map((elderly) => (
                                <div key={elderly.elderly_id} className="elderly-summary-card">
                                    <div className="card-header">
                                        <h3>{elderly.elderly_name}</h3>
                                        <span className="record-count">{elderly.total_records} records</span>
                                    </div>

                                    <div className="card-content">
                                        <p className="summary-text">{elderly.summary}</p>

                                        {elderly.key_points.length > 0 && (
                                            <div className="key-points">
                                                <h4>Key Points:</h4>
                                                <ul>
                                                    {elderly.key_points.map((point, idx) => (
                                                        <li key={idx}>{point}</li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                    </div>

                                    <div className="card-footer">
                                        <button 
                                            onClick={() => navigate(`/elderly/${elderly.elderly_id}`)}
                                            className="view-button"
                                        >
                                            View Full Profile →
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                ) : (
                    <div className="section">
                        <p>No STM records found for the selected date range.</p>
                    </div>
                )}

                {dashboardData && (
                    <div className="section metadata">
                        <p>
                            Last Generated: {new Date(dashboardData.last_generated).toLocaleString()} | 
                            Date Range: {new Date(dashboardData.date_range.start).toLocaleDateString()} - {new Date(dashboardData.date_range.end).toLocaleDateString()}
                        </p>
                    </div>
                )}

                <button onClick={() => navigate(-1)} className="back-button">
                    ← Back
                </button>
            </div>
        </div>
    );
};

export default Dashboard;