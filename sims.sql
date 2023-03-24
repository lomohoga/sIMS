-- MySQL dump 10.13  Distrib 8.0.32, for Linux (x86_64)
--
-- Host: localhost    Database: sims
-- ------------------------------------------------------
-- Server version	8.0.32-0ubuntu0.22.04.2

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `sims`
--

/*!40000 DROP DATABASE IF EXISTS `sims`*/;

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `sims` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `sims`;

--
-- Table structure for table `delivery`
--

DROP TABLE IF EXISTS `delivery`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `delivery` (
  `DeliveryID` int NOT NULL AUTO_INCREMENT,
  `ItemID` varchar(16) NOT NULL,
  `DeliveryQuantity` int NOT NULL,
  `DeliveryDate` date NOT NULL DEFAULT (curdate()),
  `ReceivedBy` varchar(30) NOT NULL,
  PRIMARY KEY (`DeliveryID`),
  KEY `DeliveryItem` (`ItemID`),
  KEY `ReceivedBy` (`ReceivedBy`),
  CONSTRAINT `delivery_ibfk_1` FOREIGN KEY (`ItemID`) REFERENCES `item` (`ItemID`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `delivery_ibfk_2` FOREIGN KEY (`ReceivedBy`) REFERENCES `user` (`Username`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `delivery`
--

LOCK TABLES `delivery` WRITE;
/*!40000 ALTER TABLE `delivery` DISABLE KEYS */;
/*!40000 ALTER TABLE `delivery` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary view structure for view `expiration`
--

DROP TABLE IF EXISTS `expiration`;
/*!50001 DROP VIEW IF EXISTS `expiration`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `expiration` AS SELECT 
 1 AS `DeliveryID`,
 1 AS `DeliveryDate`,
 1 AS `ExpirationDate`,
 1 AS `IsExpired`*/;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `item`
--

DROP TABLE IF EXISTS `item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `item` (
  `ItemID` varchar(16) NOT NULL,
  `ItemName` varchar(20) NOT NULL,
  `ItemDescription` varchar(100) NOT NULL,
  `ShelfLife` int DEFAULT NULL,
  `Price` decimal(18,2) NOT NULL,
  `Unit` varchar(20) NOT NULL DEFAULT 'units',
  PRIMARY KEY (`ItemID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `item`
--

LOCK TABLES `item` WRITE;
/*!40000 ALTER TABLE `item` DISABLE KEYS */;
/*!40000 ALTER TABLE `item` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `request`
--

DROP TABLE IF EXISTS `request`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `request` (
  `RequestID` int NOT NULL AUTO_INCREMENT,
  `RequestedBy` varchar(30) NOT NULL,
  `RequestDate` date NOT NULL DEFAULT (curdate()),
  `StatusID` int NOT NULL DEFAULT '1',
  `ApprovedBy` varchar(30) DEFAULT NULL,
  `IssuedBy` varchar(30) DEFAULT NULL,
  `ReceivedBy` varchar(30) DEFAULT NULL,
  PRIMARY KEY (`RequestID`),
  KEY `RequestedBy` (`RequestedBy`),
  KEY `Status` (`StatusID`),
  KEY `request_ibfk_4_idx` (`ApprovedBy`),
  KEY `request_ibfk_5_idx` (`IssuedBy`),
  KEY `request_ibfk_6_idx` (`ReceivedBy`),
  CONSTRAINT `request_ibfk_2` FOREIGN KEY (`RequestedBy`) REFERENCES `user` (`Username`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `request_ibfk_3` FOREIGN KEY (`StatusID`) REFERENCES `request_status` (`StatusID`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `request_ibfk_4` FOREIGN KEY (`ApprovedBy`) REFERENCES `user` (`Username`),
  CONSTRAINT `request_ibfk_5` FOREIGN KEY (`IssuedBy`) REFERENCES `user` (`Username`),
  CONSTRAINT `request_ibfk_6` FOREIGN KEY (`ReceivedBy`) REFERENCES `user` (`Username`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `request`
--

LOCK TABLES `request` WRITE;
/*!40000 ALTER TABLE `request` DISABLE KEYS */;
/*!40000 ALTER TABLE `request` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `request_items`
--

DROP TABLE IF EXISTS `request_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `request_items` (
  `RequestID` int NOT NULL,
  `ItemID` varchar(16) NOT NULL,
  `Quantity` int NOT NULL,
  PRIMARY KEY (`RequestID`,`ItemID`),
  KEY `itemID_idx` (`ItemID`),
  CONSTRAINT `itemID` FOREIGN KEY (`ItemID`) REFERENCES `item` (`ItemID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `request_items`
--

LOCK TABLES `request_items` WRITE;
/*!40000 ALTER TABLE `request_items` DISABLE KEYS */;
/*!40000 ALTER TABLE `request_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `request_status`
--

DROP TABLE IF EXISTS `request_status`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `request_status` (
  `StatusID` int NOT NULL,
  `StatusName` varchar(10) NOT NULL,
  PRIMARY KEY (`StatusID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `request_status`
--

LOCK TABLES `request_status` WRITE;
/*!40000 ALTER TABLE `request_status` DISABLE KEYS */;
INSERT INTO `request_status` VALUES (1,'Pending'),(2,'Approved'),(3,'Issued'),(4,'Completed'),(5,'Rejected');
/*!40000 ALTER TABLE `request_status` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `role`
--

DROP TABLE IF EXISTS `role`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `role` (
  `RoleID` int NOT NULL,
  `RoleName` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`RoleID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `role`
--

LOCK TABLES `role` WRITE;
/*!40000 ALTER TABLE `role` DISABLE KEYS */;
INSERT INTO `role` VALUES (0,'Admin'),(1,'Custodian'),(2,'Personnel');
/*!40000 ALTER TABLE `role` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary view structure for view `stock`
--

DROP TABLE IF EXISTS `stock`;
/*!50001 DROP VIEW IF EXISTS `stock`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `stock` AS SELECT 
 1 AS `ItemID`,
 1 AS `ItemName`,
 1 AS `ItemDescription`,
 1 AS `ShelfLife`,
 1 AS `Price`,
 1 AS `AvailableStock`,
 1 AS `Unit`*/;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user` (
  `Username` varchar(30) NOT NULL,
  `Password` varchar(64) NOT NULL,
  `FirstName` varchar(30) NOT NULL,
  `LastName` varchar(30) NOT NULL,
  `Email` varchar(64) NOT NULL,
  `RoleID` int NOT NULL,
  PRIMARY KEY (`Username`),
  KEY `RoleID` (`RoleID`),
  CONSTRAINT `user_ibfk_1` FOREIGN KEY (`RoleID`) REFERENCES `role` (`RoleID`),
  CONSTRAINT `user_chk_1` CHECK (regexp_like(`Email`,_utf8mb4'^([0-9a-z]|([0-9a-z][\\.\\-_]{1}[0-9a-z]))+@([0-9a-z\\-]+\\.)+[a-z]{2,}$'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user`
--

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
INSERT INTO `user` VALUES ('asaito','0d8dee449758d4fc3bad65c9262d30a5a85d9abeb51cccf581f683833d80ce38','Asuka','Saito','asaito@deped.gov.ph',2),('bajo','6d5a003977c7270a4183ed84926d71b1b1507ec6700f6349e4e70411312fc2a9','Braullo','Jo','braullojo.bj@gmail.com',1),('hpham','65f28cb7430292b6e09d28470d1cb1fc19c7d602b206d4ba9de3e6791fbb42a8','Hanni','Pham','braullojo.bj@gmail.com',0),('ksante','9c6880c361a20206300f0e5121caa8f68886d47e67f74a20f87d31973171972b','Rose','Santos','ksante@deped.gov.ph',2);
/*!40000 ALTER TABLE `user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Final view structure for view `expiration`
--

/*!50001 DROP VIEW IF EXISTS `expiration`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = cp850 */;
/*!50001 SET character_set_results     = cp850 */;
/*!50001 SET collation_connection      = cp850_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `expiration` AS select `delivery`.`DeliveryID` AS `DeliveryID`,`delivery`.`DeliveryDate` AS `DeliveryDate`,(`delivery`.`DeliveryDate` + interval `item`.`ShelfLife` day) AS `ExpirationDate`,coalesce(((to_days(curdate()) - to_days((`delivery`.`DeliveryDate` + interval `item`.`ShelfLife` day))) > 0),0) AS `IsExpired` from (`delivery` join `item` on((`delivery`.`ItemID` = `item`.`ItemID`))) order by `delivery`.`DeliveryID` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `stock`
--

/*!50001 DROP VIEW IF EXISTS `stock`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = cp850 */;
/*!50001 SET character_set_results     = cp850 */;
/*!50001 SET collation_connection      = cp850_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `stock` AS select `item`.`ItemID` AS `ItemID`,`item`.`ItemName` AS `ItemName`,`item`.`ItemDescription` AS `ItemDescription`,`item`.`ShelfLife` AS `ShelfLife`,`item`.`Price` AS `Price`,coalesce(sum(if(`expiration`.`IsExpired`,0,`delivery`.`DeliveryQuantity`)),0) AS `AvailableStock`,`item`.`Unit` AS `Unit` from (`item` left join (`delivery` join `expiration` on((`delivery`.`DeliveryID` = `expiration`.`DeliveryID`))) on((`item`.`ItemID` = `delivery`.`ItemID`))) group by `item`.`ItemID` order by `item`.`ItemID` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-03-22 11:18:36
