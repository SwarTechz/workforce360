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


-------Temparary Query------------------------
update workers
set is_available = true
-------------------------------------------

-- If you want to delete whole table use this command
TRUNCATE TABLE
	company_bank_details,
    company_addresses,
    company_documents,
    companies
RESTART IDENTITY;

select * from documents
select * from document_chunks
select * from chat_sessions
select * from chat_messages

TRUNCATE TABLE
	chat_sessions,
	chat_messages

TRUNCATE TABLE
    worker_documents,
	worker_skill_categories,
	worker_skill_subcategories,
    workers,
	job_postings
RESTART IDENTITY;


--Prerequsite Commands
CREATE DATABASE workforce360_db
CREATE EXTENSION IF NOT EXISTS postgis; --Enable postgis extension inside your database:

--Worker
ALTER TABLE workers
ALTER COLUMN id
SET DEFAULT gen_random_uuid();	

ALTER TABLE workers
ALTER COLUMN is_active SET DEFAULT true

--Job
ALTER TABLE job_postings
ALTER COLUMN id
SET DEFAULT gen_random_uuid();	

ALTER TABLE job_postings
ALTER COLUMN is_active SET DEFAULT true

--Company
ALTER TABLE companies
ALTER COLUMN id
SET DEFAULT gen_random_uuid();	

ALTER TABLE company_documents
ALTER COLUMN id
SET DEFAULT gen_random_uuid();	

ALTER TABLE company_addresses
ALTER COLUMN id
SET DEFAULT gen_random_uuid();	

ALTER TABLE company_bank_details
ALTER COLUMN id
SET DEFAULT gen_random_uuid();	

ALTER TABLE companies
ALTER COLUMN is_active SET DEFAULT true

ALTER TABLE industry_types
ALTER COLUMN id
SET DEFAULT gen_random_uuid();

ALTER TABLE category_skills
ALTER COLUMN id
SET DEFAULT gen_random_uuid();	

ALTER TABLE sub_category_skills
ALTER COLUMN id
SET DEFAULT gen_random_uuid();	


-- Industry Types
INSERT INTO industry_types (name, is_active)
VALUES
    ('Automobile & Transport', TRUE),
    ('Construction & Civil', TRUE),
    ('Electrical, Electronics & Plumbing', TRUE),
    ('Food & Hospitality', TRUE),
    ('Healthcare & Support', TRUE),
    ('Logistics, Retail & Warehousing', TRUE),
    ('Mechanical, Metal & Fabrication', TRUE),
    ('Plastic, Chemical & Manufacturing', TRUE),
    ('Printing, Paper & Packaging', TRUE),
    ('Textile, Garments & Leather', TRUE),
    ('Wood, Furniture & Handicrafts', TRUE),
    ('General / Unskilled Roles', TRUE)

------------ Skill Category ---------------
--1. Automobile & Transport
INSERT INTO category_skills (industry_type_id, name, is_active) VALUES
('13c43402-faa9-4f42-b295-3e26a3f8f12b', 'Drivers' , TRUE),
		('13c43402-faa9-4f42-b295-3e26a3f8f12b', 'Mechanics' , TRUE),
		('13c43402-faa9-4f42-b295-3e26a3f8f12b', 'Service Staff' , TRUE),
		('13c43402-faa9-4f42-b295-3e26a3f8f12b', 'Support Roles' , TRUE),
		('13c43402-faa9-4f42-b295-3e26a3f8f12b', 'Fuel Station Staff' , TRUE),
--2. Construction & Civil
	    ('954ac9bd-a46c-42a1-a37f-1dd35566b7a6', 'Masons' , TRUE),
		('954ac9bd-a46c-42a1-a37f-1dd35566b7a6', 'Concrete Workers' , TRUE),
		('954ac9bd-a46c-42a1-a37f-1dd35566b7a6', 'Plasterers' , TRUE),
		('954ac9bd-a46c-42a1-a37f-1dd35566b7a6', 'Steel Fixers' , TRUE),
		('954ac9bd-a46c-42a1-a37f-1dd35566b7a6', 'Scaffolders' , TRUE),
        ('954ac9bd-a46c-42a1-a37f-1dd35566b7a6', 'Painters' , TRUE),
        ('954ac9bd-a46c-42a1-a37f-1dd35566b7a6', 'Roof Workers' , TRUE),
        ('954ac9bd-a46c-42a1-a37f-1dd35566b7a6', 'Road Workers' , TRUE),
        ('954ac9bd-a46c-42a1-a37f-1dd35566b7a6', 'Survey Assistants' , TRUE),
        ('954ac9bd-a46c-42a1-a37f-1dd35566b7a6', 'Demolition Workers' , TRUE),

--3. Electrical, Electronics & Plumbing
    ('d3b139ad-918c-4fb8-993f-9eaab432dde3', 'Electricians', TRUE),
    ('d3b139ad-918c-4fb8-993f-9eaab432dde3', 'Plumbers', TRUE),
    ('d3b139ad-918c-4fb8-993f-9eaab432dde3', 'Pipefitters', TRUE),
    ('d3b139ad-918c-4fb8-993f-9eaab432dde3', 'Refrigeration & AC', TRUE),
    ('d3b139ad-918c-4fb8-993f-9eaab432dde3', 'Lift Mechanics', TRUE),
    ('d3b139ad-918c-4fb8-993f-9eaab432dde3', 'Solar Technicians', TRUE),
    ('d3b139ad-918c-4fb8-993f-9eaab432dde3', 'Cable Installers', TRUE),
    ('d3b139ad-918c-4fb8-993f-9eaab432dde3', 'Panel Technicians', TRUE),

--4. Food & Hospitality
('52d126bc-86e6-4c05-8605-e9198615a01e', 'Cooks', TRUE),
('52d126bc-86e6-4c05-8605-e9198615a01e', 'Bakers', TRUE),
('52d126bc-86e6-4c05-8605-e9198615a01e', 'Meat Workers', TRUE),
('52d126bc-86e6-4c05-8605-e9198615a01e', 'Service Staffs', TRUE),
('52d126bc-86e6-4c05-8605-e9198615a01e', 'Kitchen Helpers', TRUE),
('52d126bc-86e6-4c05-8605-e9198615a01e', 'Food Processing', TRUE),
('52d126bc-86e6-4c05-8605-e9198615a01e', 'Cold Storage Staff', TRUE),

--5. General / Unskilled Roles 
('f029fa9f-0c44-40e0-a426-774c80e44db2', 'Helpers / Assistants', TRUE),
('f029fa9f-0c44-40e0-a426-774c80e44db2', 'Loaders & Unloaders', TRUE),
('f029fa9f-0c44-40e0-a426-774c80e44db2', 'Cleaners / Janitors', TRUE),
('f029fa9f-0c44-40e0-a426-774c80e44db2', 'Housekeeping Staff', TRUE),
('f029fa9f-0c44-40e0-a426-774c80e44db2', 'Security Guards', TRUE),
('f029fa9f-0c44-40e0-a426-774c80e44db2', 'Office Boys / Peons', TRUE),
('f029fa9f-0c44-40e0-a426-774c80e44db2', 'Delivery Boys / Couriers', TRUE),
('f029fa9f-0c44-40e0-a426-774c80e44db2', 'Warehouse Staff', TRUE),
('f029fa9f-0c44-40e0-a426-774c80e44db2', 'Gardeners / Mali', TRUE),
('f029fa9f-0c44-40e0-a426-774c80e44db2', 'Attendants', TRUE),
('f029fa9f-0c44-40e0-a426-774c80e44db2', 'Parking/Toll Staff', TRUE),
('f029fa9f-0c44-40e0-a426-774c80e44db2', 'Domestic Helpers', TRUE),
('f029fa9f-0c44-40e0-a426-774c80e44db2', 'Construction Laborers', TRUE),
('f029fa9f-0c44-40e0-a426-774c80e44db2', 'Agricultural Workers', TRUE),
('f029fa9f-0c44-40e0-a426-774c80e44db2', 'Material Handlers', TRUE),
('f029fa9f-0c44-40e0-a426-774c80e44db2', 'Porters / Coolies', TRUE),

--6. Healthcare & Support
('c7421955-d21c-42eb-b8c9-229ac229b43f', 'Hospital Support', TRUE),
('c7421955-d21c-42eb-b8c9-229ac229b43f', 'Medical Transport', TRUE),
('c7421955-d21c-42eb-b8c9-229ac229b43f', 'Lab Support', TRUE),
('c7421955-d21c-42eb-b8c9-229ac229b43f', 'Sanitation Workers', TRUE),
('c7421955-d21c-42eb-b8c9-229ac229b43f', 'Nursing Assistants', TRUE),

--7. Logistics, Retail & Warehousing
('d47a64ca-c5cb-4954-995e-24e34f03ab7f', 'Warehouse Staff', TRUE),
('d47a64ca-c5cb-4954-995e-24e34f03ab7f', 'Retail Helpers', TRUE),
('d47a64ca-c5cb-4954-995e-24e34f03ab7f', 'Transport Staff', TRUE),

--8. Mechanical, Metal & Fabrication
('40830bee-e543-4189-8195-4378af827f2b', 'Welders', TRUE),
('40830bee-e543-4189-8195-4378af827f2b', 'Fitters', TRUE),
('40830bee-e543-4189-8195-4378af827f2b', 'Fabricators', TRUE),
('40830bee-e543-4189-8195-4378af827f2b', 'Metal Workers', TRUE),
('40830bee-e543-4189-8195-4378af827f2b', 'Machine Operators', TRUE),
('40830bee-e543-4189-8195-4378af827f2b', 'Tool Makers', TRUE),
('40830bee-e543-4189-8195-4378af827f2b', 'Boilermakers', TRUE),

--9. Plastic, Chemical & Manufacturing
('840dd432-8ec2-4802-8100-c86b50120219', 'Plastic Workers', TRUE),
('840dd432-8ec2-4802-8100-c86b50120219', 'Rubber Workers', TRUE),
('840dd432-8ec2-4802-8100-c86b50120219', 'Chemical Plant Staff', TRUE),
('840dd432-8ec2-4802-8100-c86b50120219', 'Surface Treatment', TRUE),
('840dd432-8ec2-4802-8100-c86b50120219', 'Packaging Line', TRUE),
('840dd432-8ec2-4802-8100-c86b50120219', 'Lab Helpers', TRUE),

--10. Printing, Paper & Packaging
('395794fc-19dc-4db9-b29c-f94544e3bc4a', 'Press Operators', TRUE),
('395794fc-19dc-4db9-b29c-f94544e3bc4a', 'Binding Staff', TRUE),
('395794fc-19dc-4db9-b29c-f94544e3bc4a', 'Packaging Workers', TRUE),
('395794fc-19dc-4db9-b29c-f94544e3bc4a', 'Paper Workers', TRUE),

--11. Textile, Garments & Leather
('5c818f3c-0afe-4d1d-afd5-738dc5fc89da', 'Tailors', TRUE),
('5c818f3c-0afe-4d1d-afd5-738dc5fc89da', 'Stitching Workers', TRUE),
('5c818f3c-0afe-4d1d-afd5-738dc5fc89da', 'Embroiderers', TRUE),
('5c818f3c-0afe-4d1d-afd5-738dc5fc89da', 'Weavers', TRUE),
('5c818f3c-0afe-4d1d-afd5-738dc5fc89da', 'Cutters', TRUE),
('5c818f3c-0afe-4d1d-afd5-738dc5fc89da', 'Dyers/Printers', TRUE),
('5c818f3c-0afe-4d1d-afd5-738dc5fc89da', 'Leather Workers', TRUE),
('5c818f3c-0afe-4d1d-afd5-738dc5fc89da', 'Repair Staff', TRUE),
('5c818f3c-0afe-4d1d-afd5-738dc5fc89da', 'Quilters', TRUE),

--12. Wood, Furniture & Handicrafts
('6abf79ba-6de6-40dc-b215-f68f9f92815b', 'Carpenters', TRUE),
('6abf79ba-6de6-40dc-b215-f68f9f92815b', 'Upholsterers', TRUE),
('6abf79ba-6de6-40dc-b215-f68f9f92815b', 'Polishers', TRUE),
('6abf79ba-6de6-40dc-b215-f68f9f92815b', 'Machine Operators', TRUE),
('6abf79ba-6de6-40dc-b215-f68f9f92815b', 'Handicraft Workers', TRUE),
('6abf79ba-6de6-40dc-b215-f68f9f92815b', 'Glass Workers', TRUE),
('6abf79ba-6de6-40dc-b215-f68f9f92815b', 'Potters', TRUE);

------------ Skill Sub Category ---------------

INSERT INTO sub_category_skills (category_skill_id, name, is_active) VALUES
--Drivers
('cd973909-d6e2-4fa7-be1a-3f8f875220f0', 'Car Driver', TRUE),
('cd973909-d6e2-4fa7-be1a-3f8f875220f0', 'Bus Driver', TRUE),
('cd973909-d6e2-4fa7-be1a-3f8f875220f0', 'Truck Driver', TRUE),
('cd973909-d6e2-4fa7-be1a-3f8f875220f0', 'Tractor Driver', TRUE),
('cd973909-d6e2-4fa7-be1a-3f8f875220f0', 'Crane Operator', TRUE),
('cd973909-d6e2-4fa7-be1a-3f8f875220f0', 'ForkLift Operator', TRUE),
('cd973909-d6e2-4fa7-be1a-3f8f875220f0', 'Others', TRUE),
-- Service Staff
('76233898-bb2a-44ee-9132-3621c1542ae7', 'Tyre Technician', TRUE),
('76233898-bb2a-44ee-9132-3621c1542ae7', 'Battery Service Worker', TRUE),
('76233898-bb2a-44ee-9132-3621c1542ae7', 'Auto Body Repair Technician', TRUE),
('76233898-bb2a-44ee-9132-3621c1542ae7', 'Others', TRUE),
-- Support Roles
('46523588-9705-4534-a9da-1dbd8a83d0b5', 'Vehicle Washer', TRUE),
('46523588-9705-4534-a9da-1dbd8a83d0b5', 'Garage Helper', TRUE),
('46523588-9705-4534-a9da-1dbd8a83d0b5', 'Spare Parts Handler', TRUE),
('46523588-9705-4534-a9da-1dbd8a83d0b5', 'Others', TRUE),
-- Fuel Station Staff
('dc5da99e-f074-4902-9628-9b3352a565b6', 'Pump Attendant', TRUE),
('dc5da99e-f074-4902-9628-9b3352a565b6', 'Air/Water Service Worker', TRUE),
('dc5da99e-f074-4902-9628-9b3352a565b6', 'Others', TRUE),
--Mechanics
('d06ec5af-afb9-4a49-8f35-a9cb40997a25', 'Two-Wheeler Mechanic', TRUE),
('d06ec5af-afb9-4a49-8f35-a9cb40997a25', 'Four-Wheeler Mechanic', TRUE),
('d06ec5af-afb9-4a49-8f35-a9cb40997a25', 'Heavy Vehicle Mechanic', TRUE),
('d06ec5af-afb9-4a49-8f35-a9cb40997a25', 'Others', TRUE),
--Masons
('a3b8fa26-ad32-4b51-9ae7-3910ac12a5c4', 'Brick Mason', TRUE),
('a3b8fa26-ad32-4b51-9ae7-3910ac12a5c4', 'Tile Mason', TRUE),
('a3b8fa26-ad32-4b51-9ae7-3910ac12a5c4', 'Marble Mason', TRUE),
('a3b8fa26-ad32-4b51-9ae7-3910ac12a5c4', 'Stone Mason', TRUE),
('a3b8fa26-ad32-4b51-9ae7-3910ac12a5c4', 'Others', TRUE),
--Electricians
('7b2bd549-f8f7-4b0d-918b-9dd312e536ef', 'Domestic Electrician', TRUE),
('7b2bd549-f8f7-4b0d-918b-9dd312e536ef', 'Industrial Electrician', TRUE),
('7b2bd549-f8f7-4b0d-918b-9dd312e536ef', 'High Voltage Electrician', TRUE),
('7b2bd549-f8f7-4b0d-918b-9dd312e536ef', 'Others', TRUE),
--Cooks
('00985941-44f7-463f-b7fc-f9ce6edfbc1d', 'Restaurant Cook', TRUE),
('00985941-44f7-463f-b7fc-f9ce6edfbc1d', 'Hotel Cook', TRUE),
('00985941-44f7-463f-b7fc-f9ce6edfbc1d', 'Industrial Mess Cook', TRUE),
('00985941-44f7-463f-b7fc-f9ce6edfbc1d', 'Catering Cook', TRUE),
('00985941-44f7-463f-b7fc-f9ce6edfbc1d', 'Others', TRUE),
--Helpers / Assistants
('e84a867b-20be-4f9b-b89c-cd797aedb282', 'Factory Helper', TRUE),
('e84a867b-20be-4f9b-b89c-cd797aedb282', 'Construction Helper', TRUE),
('e84a867b-20be-4f9b-b89c-cd797aedb282', 'Workshop Helper', TRUE),
('e84a867b-20be-4f9b-b89c-cd797aedb282', 'Office Helper', TRUE),
('e84a867b-20be-4f9b-b89c-cd797aedb282', 'Others', TRUE),
--Hospital Support
('514934e7-8008-466d-9e5d-9f581dec02e9', 'Ward Boy', TRUE),
('514934e7-8008-466d-9e5d-9f581dec02e9', 'Patient Attendant', TRUE),
('514934e7-8008-466d-9e5d-9f581dec02e9', 'Hospital Cleaner', TRUE),
('514934e7-8008-466d-9e5d-9f581dec02e9', 'Others', TRUE),
--Carpenters
('10dc68b0-b9c2-4048-9077-8fb3adfb0137', 'Furniture Carpenter', TRUE),
('10dc68b0-b9c2-4048-9077-8fb3adfb0137', 'Modular Carpenter', TRUE),
('10dc68b0-b9c2-4048-9077-8fb3adfb0137', 'Construction Carpenter', TRUE),
('10dc68b0-b9c2-4048-9077-8fb3adfb0137', 'Others', TRUE)
ON CONFLICT (category_skill_id, name) DO NOTHING;
		