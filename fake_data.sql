INSERT INTO users (uid, username, email, phone, address) VALUES
('1b9d6bcd-bbfd-4b2d-9b5d-8f1c2a7e1a01','user1','user1@test.com','+26134000001','Analakely'),
('2c1a7e92-5f3a-4f4c-8c1d-2e7b9c0a2b02','user2','user2@test.com','+26134000002','Isoraka'),
('3d2b8f03-6a4b-4e5d-9d2e-3f8c1d0b3c03','user3','user3@test.com','+26134000003','Ankorondrano'),
('4e3c9014-7b5c-4f6e-ae3f-4a9d2e1c4d04','user4','user4@test.com','+26134000004','Ivandry'),
('5f4da125-8c6d-4a7f-bf40-5b0e3f2d5e05','user5','user5@test.com','+26134000005','Ambohijatovo'),
('6a5eb236-9d7e-4b80-c051-6c1f403e6f06','user6','user6@test.com','+26134000006','67Ha'),
('7b6fc347-ae8f-4c91-d162-7d20514f7007','user7','user7@test.com','+26134000007','Anosy'),
('8c70d458-bf90-4da2-e273-8e3162608108','user8','user8@test.com','+26134000008','Mahamasina'),
('9d81e569-c0a1-4eb3-f384-9f4273719209','user9','user9@test.com','+26134000009','Tsaralalana'),
('ae92f67a-d1b2-4fc4-0495-a0538482a10a','user10','user10@test.com','+26134000010','Antsakaviro'),
('bf03f78b-e2c3-40d5-15a6-b1649593b20b','user11','user11@test.com','+26134000011','Ampandrana'),
('c014089c-f3d4-41e6-26b7-c275a6a4c30c','user12','user12@test.com','+26134000012','Andohalo'),
('d12519ad-04e5-42f7-37c8-d386b7b5d40d','user13','user13@test.com','+26134000013','Faravohitra'),
('e2362abe-15f6-4308-48d9-e497c8c6e50e','user14','user14@test.com','+26134000014','Ambanidia'),
('f3473bcf-26f7-4419-59ea-f5a8d9d7f60f','user15','user15@test.com','+26134000015','Ambohipo');

INSERT INTO restaurants (id, name, cuisine, rating, delivery_time, menu) VALUES
('550e8400-e29b-41d4-a716-446655440001','Hot Pizza','Italian',4.5,'30 min','["pizza","pasta"]'),
('550e8400-e29b-41d4-a716-446655440002','Quick Bites','Fast Food',4.0,'20 min','["burger","fries"]'),
('550e8400-e29b-41d4-a716-446655440003','Sushi Go','Japanese',4.7,'40 min','["sushi","ramen"]'),
('550e8400-e29b-41d4-a716-446655440004','Madagascar Grill','Local',4.3,'35 min','["romazava","ravitoto"]'),
('550e8400-e29b-41d4-a716-446655440005','Tasty Curry','Indian',4.2,'45 min','["curry","naan"]');


INSERT INTO orders (order_id, user_id, item, status, total, currency) VALUES
('550e8400-e29b-41d4-a716-446655441001','1b9d6bcd-bbfd-4b2d-9b5d-8f1c2a7e1a01','pizza','delivered',25000,'MGA'),
('550e8400-e29b-41d4-a716-446655441002','2c1a7e92-5f3a-4f4c-8c1d-2e7b9c0a2b02','burger','pending',15000,'MGA'),
('550e8400-e29b-41d4-a716-446655441003','3d2b8f03-6a4b-4e5d-9d2e-3f8c1d0b3c03','sushi','delivered',40000,'MGA'),
('550e8400-e29b-41d4-a716-446655441004','4e3c9014-7b5c-4f6e-ae3f-4a9d2e1c4d04','romazava','cancelled',18000,'MGA'),
('550e8400-e29b-41d4-a716-446655441005','5f4da125-8c6d-4a7f-bf40-5b0e3f2d5e05','curry','pending',22000,'MGA');

INSERT INTO rides (ride_id, user_id, destination, pickup, status, price, currency) VALUES
('550e8400-e29b-41d4-a716-446655442001','1b9d6bcd-bbfd-4b2d-9b5d-8f1c2a7e1a01','Ivandry','Analakely','completed',8000,'MGA'),
('550e8400-e29b-41d4-a716-446655442002','2c1a7e92-5f3a-4f4c-8c1d-2e7b9c0a2b02','Anosy','Isoraka','confirmed',5000,'MGA'),
('550e8400-e29b-41d4-a716-446655442003','3d2b8f03-6a4b-4e5d-9d2e-3f8c1d0b3c03','67Ha','Ankorondrano','completed',7000,'MGA'),
('550e8400-e29b-41d4-a716-446655442004','4e3c9014-7b5c-4f6e-ae3f-4a9d2e1c4d04','Mahamasina','Ivandry','cancelled',6000,'MGA'),
('550e8400-e29b-41d4-a716-446655442005','5f4da125-8c6d-4a7f-bf40-5b0e3f2d5e05','Tsaralalana','Ambohijatovo','completed',5500,'MGA');