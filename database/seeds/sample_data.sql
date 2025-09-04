-- ElderComp Sample Data for Testing
-- This file contains sample data for HCM and LTM modules
-- WARNING: This is for development/testing only - contains mock medical data

SET search_path TO eldercomp, public;

-- ============================================================================
-- SAMPLE ELDERLY PROFILES
-- ============================================================================

-- Insert sample elderly profiles
INSERT INTO elderly_profiles (id, first_name, last_name, preferred_name, date_of_birth, gender, phone_number, emergency_contact_name, emergency_contact_phone, address) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'Margaret', 'Chen', 'Maggie', '1935-03-15', 'Female', '+65-9123-4567', 'David Chen (Son)', '+65-9876-5432', '123 Orchard Road, Singapore 238874'),
('550e8400-e29b-41d4-a716-446655440002', 'Robert', 'Lim', 'Uncle Bob', '1940-07-22', 'Male', '+65-8234-5678', 'Susan Lim (Daughter)', '+65-9765-4321', '456 Toa Payoh Central, Singapore 310456'),
('550e8400-e29b-41d4-a716-446655440003', 'Siti', 'Rahman', 'Nenek Siti', '1938-11-08', 'Female', '+65-9345-6789', 'Ahmad Rahman (Son)', '+65-8654-3210', '789 Tampines Street 71, Singapore 520789');

-- ============================================================================
-- LTM SAMPLE DATA
-- ============================================================================

-- Personal preferences for Margaret Chen
INSERT INTO personal_preferences (elderly_id, category, preference_name, preference_value, importance_level, notes) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'food', 'Favorite Cuisine', 'Teochew porridge', 9, 'Especially loves fish porridge from Maxwell Food Centre'),
('550e8400-e29b-41d4-a716-446655440001', 'food', 'Dietary Restriction', 'Low sodium', 8, 'Doctor recommended due to hypertension'),
('550e8400-e29b-41d4-a716-446655440001', 'activity', 'Hobby', 'Mahjong', 7, 'Plays every Tuesday and Friday with neighbors'),
('550e8400-e29b-41d4-a716-446655440001', 'music', 'Favorite Genre', 'Hokkien oldies', 6, 'Enjoys Teresa Teng songs'),
('550e8400-e29b-41d4-a716-446655440001', 'activity', 'Exercise', 'Tai Chi', 8, 'Morning routine at void deck');

-- Personal preferences for Robert Lim
INSERT INTO personal_preferences (elderly_id, category, preference_name, preference_value, importance_level, notes) VALUES
('550e8400-e29b-41d4-a716-446655440002', 'food', 'Favorite Dish', 'Hainanese Chicken Rice', 8, 'From Tian Tian stall at Maxwell'),
('550e8400-e29b-41d4-a716-446655440002', 'activity', 'Hobby', 'Reading newspapers', 9, 'Reads Lianhe Zaobao and Straits Times daily'),
('550e8400-e29b-41d4-a716-446655440002', 'activity', 'Social', 'Coffee shop gatherings', 7, 'Meets friends at void deck coffee shop'),
('550e8400-e29b-41d4-a716-446655440002', 'entertainment', 'TV Shows', 'Channel 8 dramas', 6, 'Watches evening dramas religiously');

-- Family relationships
INSERT INTO relationships (elderly_id, contact_name, relationship_type, phone_number, email, notes, is_primary_contact, is_emergency_contact) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'David Chen', 'family', '+65-9876-5432', 'david.chen@email.com', 'Eldest son, visits twice a week', true, true),
('550e8400-e29b-41d4-a716-446655440001', 'Linda Chen', 'family', '+65-8765-4321', 'linda.chen@email.com', 'Daughter-in-law, very caring', false, false),
('550e8400-e29b-41d4-a716-446655440001', 'Amy Chen', 'family', '+65-9654-3210', 'amy.chen@email.com', 'Granddaughter, university student', false, false),
('550e8400-e29b-41d4-a716-446655440001', 'Mrs. Wong', 'neighbor', '+65-9543-2109', null, 'Mahjong partner, lives next door', false, false),
('550e8400-e29b-41d4-a716-446655440002', 'Susan Lim', 'family', '+65-9765-4321', 'susan.lim@email.com', 'Only daughter, very attentive', true, true),
('550e8400-e29b-41d4-a716-446655440002', 'Michael Tan', 'family', '+65-8654-3210', 'michael.tan@email.com', 'Son-in-law, helps with errands', false, false);

-- Life memories
INSERT INTO life_memories (elderly_id, memory_title, memory_content, memory_date, memory_category, importance_level) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'Wedding Day', 'Married my late husband at Thian Hock Keng Temple in 1958. It was a simple ceremony but filled with joy. We had our wedding photos taken at the temple steps.', '1958-05-20', 'family', 10),
('550e8400-e29b-41d4-a716-446655440001', 'First Job', 'Started working as a seamstress at a textile factory in Chinatown when I was 18. Learned to sew beautiful cheongsams and made many friends there.', '1953-01-15', 'career', 8),
('550e8400-e29b-41d4-a716-446655440001', 'Son''s Birth', 'David was born at KK Hospital. I remember holding him for the first time - he was so tiny and perfect. My husband cried tears of joy.', '1960-03-10', 'family', 10),
('550e8400-e29b-41d4-a716-446655440002', 'National Service', 'Served in the Singapore Armed Forces from 1960-1962. Made lifelong friends and learned discipline. Proud to serve my country during its early years.', '1960-08-01', 'achievement', 9),
('550e8400-e29b-41d4-a716-446655440002', 'Retirement Party', 'After 35 years as a bank clerk, my colleagues threw me a wonderful retirement party at the Raffles Hotel. Felt appreciated and loved.', '1995-12-15', 'career', 8);

-- Daily routines
INSERT INTO daily_routines (elderly_id, routine_name, routine_description, time_of_day, frequency, notes) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'Morning Tai Chi', 'Practice Tai Chi at void deck with neighbors', '07:00:00', 'daily', 'Weather permitting, moves to covered area when raining'),
('550e8400-e29b-41d4-a716-446655440001', 'Afternoon Nap', 'Rest after lunch', '14:00:00', 'daily', 'Usually 1-2 hours'),
('550e8400-e29b-41d4-a716-446655440001', 'Evening TV', 'Watch Channel 8 news and dramas', '19:00:00', 'daily', 'Favorite programs from 7-10 PM'),
('550e8400-e29b-41d4-a716-446655440001', 'Mahjong Session', 'Play mahjong with neighbors', '14:30:00', 'twice weekly', 'Tuesdays and Fridays'),
('550e8400-e29b-41d4-a716-446655440002', 'Morning Walk', 'Walk around the neighborhood', '06:30:00', 'daily', 'Usually 30-45 minutes'),
('550e8400-e29b-41d4-a716-446655440002', 'Newspaper Reading', 'Read daily newspapers', '08:00:00', 'daily', 'Lianhe Zaobao and Straits Times'),
('550e8400-e29b-41d4-a716-446655440002', 'Coffee Shop Visit', 'Meet friends at void deck coffee shop', '10:00:00', 'daily', 'Social time with neighbors');

-- ============================================================================
-- HCM SAMPLE DATA (WITH ENCRYPTION)
-- ============================================================================

-- Medical records (encrypted sensitive content)
INSERT INTO medical_records (elderly_id, record_type, record_title, record_content_encrypted, record_date, healthcare_provider, sensitivity_level) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'diagnosis', 'Hypertension Diagnosis', encrypt_sensitive_data('Patient diagnosed with Stage 1 hypertension. Blood pressure readings consistently above 140/90. Recommended lifestyle changes and medication.'), '2020-03-15', 'Dr. Tan Wei Ming, Raffles Medical', 'confidential'),
('550e8400-e29b-41d4-a716-446655440001', 'diagnosis', 'Diabetes Type 2', encrypt_sensitive_data('Type 2 diabetes mellitus diagnosed. HbA1c level at 7.2%. Patient counseled on diet management and prescribed metformin.'), '2021-06-20', 'Dr. Sarah Lim, Singapore General Hospital', 'confidential'),
('550e8400-e29b-41d4-a716-446655440001', 'lab_result', 'Annual Blood Test', encrypt_sensitive_data('Cholesterol: 220 mg/dL (slightly elevated), Blood sugar: 145 mg/dL (controlled), Kidney function: Normal'), '2023-08-10', 'Raffles Medical Laboratory', 'private'),
('550e8400-e29b-41d4-a716-446655440002', 'diagnosis', 'Osteoarthritis', encrypt_sensitive_data('Mild osteoarthritis in both knees. X-ray shows minor joint space narrowing. Recommended physiotherapy and pain management.'), '2022-01-12', 'Dr. Kumar Raj, Tan Tock Seng Hospital', 'confidential'),
('550e8400-e29b-41d4-a716-446655440002', 'procedure', 'Cataract Surgery', encrypt_sensitive_data('Successful cataract surgery on right eye. Intraocular lens implanted. Post-operative recovery excellent.'), '2023-04-18', 'Dr. Jennifer Wong, Singapore National Eye Centre', 'private');

-- Current medications (encrypted)
INSERT INTO medications (elderly_id, medication_name_encrypted, dosage_encrypted, frequency_encrypted, prescribing_doctor, start_date, is_active, notes_encrypted) VALUES
('550e8400-e29b-41d4-a716-446655440001', encrypt_sensitive_data('Amlodipine'), encrypt_sensitive_data('5mg'), encrypt_sensitive_data('Once daily'), 'Dr. Tan Wei Ming', '2020-03-15', true, encrypt_sensitive_data('Take in the morning with food')),
('550e8400-e29b-41d4-a716-446655440001', encrypt_sensitive_data('Metformin'), encrypt_sensitive_data('500mg'), encrypt_sensitive_data('Twice daily'), 'Dr. Sarah Lim', '2021-06-20', true, encrypt_sensitive_data('Take with meals to reduce stomach upset')),
('550e8400-e29b-41d4-a716-446655440001', encrypt_sensitive_data('Atorvastatin'), encrypt_sensitive_data('20mg'), encrypt_sensitive_data('Once daily at bedtime'), 'Dr. Tan Wei Ming', '2022-01-10', true, encrypt_sensitive_data('For cholesterol management')),
('550e8400-e29b-41d4-a716-446655440002', encrypt_sensitive_data('Paracetamol'), encrypt_sensitive_data('500mg'), encrypt_sensitive_data('As needed'), 'Dr. Kumar Raj', '2022-01-12', true, encrypt_sensitive_data('For joint pain, maximum 4 times daily')),
('550e8400-e29b-41d4-a716-446655440002', encrypt_sensitive_data('Glucosamine'), encrypt_sensitive_data('1500mg'), encrypt_sensitive_data('Once daily'), 'Dr. Kumar Raj', '2022-02-01', true, encrypt_sensitive_data('Joint health supplement'));

-- Medical conditions (encrypted)
INSERT INTO medical_conditions (elderly_id, condition_name_encrypted, diagnosis_date, severity, status, treating_physician, notes_encrypted) VALUES
('550e8400-e29b-41d4-a716-446655440001', encrypt_sensitive_data('Essential Hypertension'), '2020-03-15', 'moderate', 'managed', 'Dr. Tan Wei Ming', encrypt_sensitive_data('Well controlled with medication and lifestyle changes')),
('550e8400-e29b-41d4-a716-446655440001', encrypt_sensitive_data('Type 2 Diabetes Mellitus'), '2021-06-20', 'mild', 'managed', 'Dr. Sarah Lim', encrypt_sensitive_data('Good glycemic control with metformin and diet')),
('550e8400-e29b-41d4-a716-446655440001', encrypt_sensitive_data('Hypercholesterolemia'), '2022-01-10', 'mild', 'managed', 'Dr. Tan Wei Ming', encrypt_sensitive_data('Responding well to statin therapy')),
('550e8400-e29b-41d4-a716-446655440002', encrypt_sensitive_data('Osteoarthritis - Bilateral Knees'), '2022-01-12', 'mild', 'managed', 'Dr. Kumar Raj', encrypt_sensitive_data('Symptoms controlled with physiotherapy and analgesics')),
('550e8400-e29b-41d4-a716-446655440002', encrypt_sensitive_data('Age-related Cataract'), '2022-11-05', 'moderate', 'resolved', 'Dr. Jennifer Wong', encrypt_sensitive_data('Right eye surgery completed, left eye stable'));

-- Allergies (encrypted)
INSERT INTO allergies (elderly_id, allergen_encrypted, reaction_type, symptoms_encrypted, discovered_date, is_active, notes_encrypted) VALUES
('550e8400-e29b-41d4-a716-446655440001', encrypt_sensitive_data('Penicillin'), 'moderate', encrypt_sensitive_data('Skin rash, itching, mild swelling'), '1975-08-20', true, encrypt_sensitive_data('Discovered during treatment for pneumonia')),
('550e8400-e29b-41d4-a716-446655440001', encrypt_sensitive_data('Shellfish'), 'mild', encrypt_sensitive_data('Stomach upset, nausea'), '1990-12-15', true, encrypt_sensitive_data('Avoid crab, prawns, lobster')),
('550e8400-e29b-41d4-a716-446655440002', encrypt_sensitive_data('Aspirin'), 'mild', encrypt_sensitive_data('Stomach irritation, heartburn'), '2010-05-10', true, encrypt_sensitive_data('Use alternative pain relievers'));

-- Healthcare appointments
INSERT INTO healthcare_appointments (elderly_id, appointment_type, healthcare_provider, appointment_date, duration_minutes, purpose_encrypted, notes_encrypted, follow_up_required, follow_up_date) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'Regular Checkup', 'Dr. Tan Wei Ming, Raffles Medical', '2024-01-15 10:00:00+08', 30, encrypt_sensitive_data('Routine diabetes and hypertension monitoring'), encrypt_sensitive_data('Blood pressure well controlled, HbA1c stable at 6.8%'), true, '2024-04-15'),
('550e8400-e29b-41d4-a716-446655440001', 'Specialist Consultation', 'Dr. Sarah Lim, SGH Endocrinology', '2024-02-20 14:30:00+08', 45, encrypt_sensitive_data('Diabetes management review'), encrypt_sensitive_data('Medication adjustment, dietary counseling provided'), true, '2024-08-20'),
('550e8400-e29b-41d4-a716-446655440002', 'Physiotherapy', 'Ms. Rachel Ng, TTSH Physiotherapy', '2024-01-10 09:00:00+08', 60, encrypt_sensitive_data('Knee osteoarthritis management'), encrypt_sensitive_data('Good progress with exercises, pain reduced'), true, '2024-02-07'),
('550e8400-e29b-41d4-a716-446655440002', 'Eye Examination', 'Dr. Jennifer Wong, SNEC', '2024-03-05 11:00:00+08', 30, encrypt_sensitive_data('Post-cataract surgery follow-up'), encrypt_sensitive_data('Excellent healing, vision 20/25'), false, null);

-- ============================================================================
-- MEMORY CONTEXTS FOR TESTING
-- ============================================================================

-- Sample memory contexts linking conversations to LTM/HCM data
INSERT INTO memory_contexts (elderly_id, context_type, reference_id, context_summary, relevance_score) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'ltm', '550e8400-e29b-41d4-a716-446655440001', 'Discussion about favorite foods and dietary preferences', 0.85),
('550e8400-e29b-41d4-a716-446655440001', 'hcm', '550e8400-e29b-41d4-a716-446655440001', 'Conversation about medication schedule and health monitoring', 0.92),
('550e8400-e29b-41d4-a716-446655440002', 'ltm', '550e8400-e29b-41d4-a716-446655440002', 'Chat about daily routines and social activities', 0.78),
('550e8400-e29b-41d4-a716-446655440002', 'hcm', '550e8400-e29b-41d4-a716-446655440002', 'Discussion about knee pain and physiotherapy progress', 0.88);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Log successful data insertion
DO $$
DECLARE
    profile_count INTEGER;
    ltm_records INTEGER;
    hcm_records INTEGER;
BEGIN
    SELECT COUNT(*) INTO profile_count FROM elderly_profiles;
    SELECT COUNT(*) INTO ltm_records FROM personal_preferences;
    SELECT COUNT(*) INTO hcm_records FROM medical_records;
    
    RAISE NOTICE 'Sample data insertion completed successfully';
    RAISE NOTICE 'Elderly profiles: %', profile_count;
    RAISE NOTICE 'LTM records (preferences): %', ltm_records;
    RAISE NOTICE 'HCM records (medical): %', hcm_records;
    RAISE NOTICE 'Note: Medical data is encrypted for privacy protection';
END $$;
