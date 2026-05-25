select * from companies
select * from company_addresses
select * from company_documents
select * from company_bank_details
select * from industry_types
select * from category_skills
select * from sub_category_skills 
select * from job_postings
select * from workers
select * from worker_skill_categories
select * from worker_skill_subcategories
select * from worker_documents

-- If you want to delete whole table use this command
TRUNCATE TABLE
	sub_category_skills,
	category_skills,
	job_postings,
	worker_skill_categories,
	worker_skill_subcategories,
	industry_types,
	company_bank_details,
    company_addresses,
    company_documents,
    companies
RESTART IDENTITY;

-- Industry Types
INSERT INTO industry_types (name, tier, is_active)
VALUES
    ('Automobile & Transport', 'Tier 2', TRUE),
    ('Electrical, Electronics & Plumbing', 'Tier 2',TRUE)

------------ Skill Category ---------------
--1. Automobile & Transport
INSERT INTO category_skills (industry_type_id, name, tier, is_active) VALUES
		('7de4e9df-4ee1-48f2-a101-3d50c34c052b', 'Drivers' ,'Tier 2', TRUE),
		('7de4e9df-4ee1-48f2-a101-3d50c34c052b', 'Mechanics' ,'Tier 2', TRUE),
		('7de4e9df-4ee1-48f2-a101-3d50c34c052b', 'Service Staff' ,'Tier 2', TRUE),
		('7de4e9df-4ee1-48f2-a101-3d50c34c052b', 'Support Roles' ,'Tier 2', TRUE),
		('7de4e9df-4ee1-48f2-a101-3d50c34c052b', 'Fuel Station Staff' ,'Tier 2', TRUE),

--3. Electrical, Electronics & Plumbing
    ('7b14c107-e529-499d-aee6-8a7b4b4b31a6', 'Electricians','Tier 2', TRUE),
    ('7b14c107-e529-499d-aee6-8a7b4b4b31a6', 'Plumbers','Tier 2', TRUE),
    ('7b14c107-e529-499d-aee6-8a7b4b4b31a6', 'Pipefitters','Tier 2', TRUE),
    ('7b14c107-e529-499d-aee6-8a7b4b4b31a6', 'Refrigeration & AC','Tier 2', TRUE),
    ('7b14c107-e529-499d-aee6-8a7b4b4b31a6', 'Lift Mechanics','Tier 2', TRUE),
    ('7b14c107-e529-499d-aee6-8a7b4b4b31a6', 'Solar Technicians','Tier 2', TRUE),
    ('7b14c107-e529-499d-aee6-8a7b4b4b31a6', 'Cable Installers','Tier 2', TRUE),
    ('7b14c107-e529-499d-aee6-8a7b4b4b31a6', 'Panel Technicians','Tier 2', TRUE)

------------ Skill Sub Category ---------------
INSERT INTO sub_category_skills (category_skill_id, name, is_active) VALUES
--Drivers
('35339653-569b-4bc5-a283-19f67e216b6a', 'Car Driver', TRUE),
('35339653-569b-4bc5-a283-19f67e216b6a', 'Bus Driver', TRUE),
('35339653-569b-4bc5-a283-19f67e216b6a', 'Truck Driver', TRUE),
('35339653-569b-4bc5-a283-19f67e216b6a', 'Tractor Driver', TRUE),
('35339653-569b-4bc5-a283-19f67e216b6a', 'Crane Operator', TRUE),
('35339653-569b-4bc5-a283-19f67e216b6a', 'ForkLift Operator', TRUE),
('35339653-569b-4bc5-a283-19f67e216b6a', 'Others', TRUE),
--Mechanics
('6419d56c-ecf4-4b83-98f2-c08b5a8f9557', 'Two-Wheeler Mechanic', TRUE),
('6419d56c-ecf4-4b83-98f2-c08b5a8f9557', 'Four-Wheeler Mechanic', TRUE),
('6419d56c-ecf4-4b83-98f2-c08b5a8f9557', 'Heavy Vehicle Mechanic', TRUE),
('6419d56c-ecf4-4b83-98f2-c08b5a8f9557', 'Others', TRUE),
-- Service Staff
('f3d2d12d-51a9-4788-b705-efe0f304cb85', 'Tyre Technician', TRUE),
('f3d2d12d-51a9-4788-b705-efe0f304cb85', 'Battery Service Worker', TRUE),
('f3d2d12d-51a9-4788-b705-efe0f304cb85', 'Auto Body Repair Technician', TRUE),
('f3d2d12d-51a9-4788-b705-efe0f304cb85', 'Others', TRUE),
-- Support Roles
('747299b8-3b5a-4b36-926b-3a3a2d638295', 'Vehicle Washer', TRUE),
('747299b8-3b5a-4b36-926b-3a3a2d638295', 'Garage Helper', TRUE),
('747299b8-3b5a-4b36-926b-3a3a2d638295', 'Spare Parts Handler', TRUE),
('747299b8-3b5a-4b36-926b-3a3a2d638295', 'Others', TRUE),
-- Fuel Station Staff
('46d3cc5b-c3f2-4e62-9148-347401038117', 'Pump Attendant', TRUE),
('46d3cc5b-c3f2-4e62-9148-347401038117', 'Air/Water Service Worker', TRUE),
('46d3cc5b-c3f2-4e62-9148-347401038117', 'Others', TRUE),