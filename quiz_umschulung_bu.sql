-- MySQL dump 10.13  Distrib 8.0.45, for Linux (x86_64)
--
-- Host: localhost    Database: quiz_umschulung
-- ------------------------------------------------------
-- Server version	8.0.45-0ubuntu0.24.04.1

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
-- Table structure for table `antwort`
--

DROP TABLE IF EXISTS `antwort`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `antwort` (
  `antwort_id` int NOT NULL AUTO_INCREMENT,
  `frage_id` int NOT NULL,
  `antworttext` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `ist_korrekt` tinyint(1) NOT NULL,
  PRIMARY KEY (`antwort_id`),
  KEY `frage_id` (`frage_id`),
  CONSTRAINT `antwort_ibfk_1` FOREIGN KEY (`frage_id`) REFERENCES `frage` (`frage_id`)
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `antwort`
--

LOCK TABLES `antwort` WRITE;
/*!40000 ALTER TABLE `antwort` DISABLE KEYS */;
/*!40000 ALTER TABLE `antwort` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `benutzer`
--

DROP TABLE IF EXISTS `benutzer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `benutzer` (
  `benutzer_id` int NOT NULL AUTO_INCREMENT,
  `kuerzel` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `passwort_hash` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  PRIMARY KEY (`benutzer_id`),
  UNIQUE KEY `kuerzel` (`kuerzel`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `benutzer`
--

LOCK TABLES `benutzer` WRITE;
/*!40000 ALTER TABLE `benutzer` DISABLE KEYS */;
INSERT INTO `benutzer` VALUES (1,'test','test','$2b$12$bqi.H5Nk6oPNJ0YfBK3ZOuzCO1BAcG2hhg3OGYj345xi/WwVJbQdW');
/*!40000 ALTER TABLE `benutzer` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `detail`
--

DROP TABLE IF EXISTS `detail`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `detail` (
  `detail_id` int NOT NULL AUTO_INCREMENT,
  `sitzung_id` int NOT NULL,
  `frage_id` int NOT NULL,
  `war_korrekt` tinyint(1) NOT NULL,
  PRIMARY KEY (`detail_id`),
  KEY `sitzung_id` (`sitzung_id`),
  KEY `frage_id` (`frage_id`),
  CONSTRAINT `detail_ibfk_1` FOREIGN KEY (`sitzung_id`) REFERENCES `sitzung` (`sitzung_id`),
  CONSTRAINT `detail_ibfk_2` FOREIGN KEY (`frage_id`) REFERENCES `frage` (`frage_id`)
) ENGINE=InnoDB AUTO_INCREMENT=37 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `detail`
--

LOCK TABLES `detail` WRITE;
/*!40000 ALTER TABLE `detail` DISABLE KEYS */;
/*!40000 ALTER TABLE `detail` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `frage`
--

DROP TABLE IF EXISTS `frage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `frage` (
  `frage_id` int NOT NULL AUTO_INCREMENT,
  `fragetext` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `erklaerung` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `typ` enum('MC','FT') COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'MC',
  PRIMARY KEY (`frage_id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `frage`
--

LOCK TABLES `frage` WRITE;
/*!40000 ALTER TABLE `frage` DISABLE KEYS */;
/*!40000 ALTER TABLE `frage` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `frage_kategorie`
--

DROP TABLE IF EXISTS `frage_kategorie`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `frage_kategorie` (
  `frage_id` int NOT NULL,
  `kategorie_id` int NOT NULL,
  PRIMARY KEY (`frage_id`,`kategorie_id`),
  KEY `kategorie_id` (`kategorie_id`),
  CONSTRAINT `frage_kategorie_ibfk_1` FOREIGN KEY (`frage_id`) REFERENCES `frage` (`frage_id`) ON DELETE CASCADE,
  CONSTRAINT `frage_kategorie_ibfk_2` FOREIGN KEY (`kategorie_id`) REFERENCES `kategorie` (`kategorie_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `frage_kategorie`
--

LOCK TABLES `frage_kategorie` WRITE;
/*!40000 ALTER TABLE `frage_kategorie` DISABLE KEYS */;
/*!40000 ALTER TABLE `frage_kategorie` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary view structure for view `frage_mit_kategorie`
--

DROP TABLE IF EXISTS `frage_mit_kategorie`;
/*!50001 DROP VIEW IF EXISTS `frage_mit_kategorie`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `frage_mit_kategorie` AS SELECT 
 1 AS `frage_id`,
 1 AS `fragetext`,
 1 AS `erklaerung`,
 1 AS `typ`,
 1 AS `kategorie_id`,
 1 AS `bezeichnung`*/;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `kategorie`
--

DROP TABLE IF EXISTS `kategorie`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kategorie` (
  `kategorie_id` int NOT NULL AUTO_INCREMENT,
  `bezeichnung` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  PRIMARY KEY (`kategorie_id`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kategorie`
--

LOCK TABLES `kategorie` WRITE;
/*!40000 ALTER TABLE `kategorie` DISABLE KEYS */;
INSERT INTO `kategorie` VALUES (1,'Gemischt (alle Fragen)'),(2,'Grundkenntnisse und Fertigkeiten in den Bereichen Elektronik und Informationstechnik herausbilden'),(3,'Client-Server-Systeme konfigurieren'),(4,'Daten in Datenbanken verwalten'),(5,'Programme entwickeln'),(6,'Netzwerkkomponenten verbinden'),(7,'Büro- und Homeoffice-Arbeitsplätze planen und installieren (ITSE)'),(8,'Büro- und Homeoffice-Arbeitsplätze planen und installieren (KIT)'),(9,'Büro- und Homeoffice-Arbeitsplätze planen und installieren (FIS)'),(10,'Prüfungsvorbereitung AP I - IT'),(11,'Prüfungsvorbereitung AP I - WISO'),(12,'Prüfungsvorbereitung AP II - IT (ITSE)'),(13,'Prüfungsvorbereitung AP II - IT (KIT)'),(14,'Prüfungsvorbereitung AP II - IT (FIS)'),(15,'Prüfungsvorbereitung AP II - WISO (alle Berufsrichtungen)');
/*!40000 ALTER TABLE `kategorie` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sitzung`
--

DROP TABLE IF EXISTS `sitzung`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sitzung` (
  `sitzung_id` int NOT NULL AUTO_INCREMENT,
  `benutzer_id` int NOT NULL,
  `kategorie_id` int DEFAULT NULL,
  `punkte` int DEFAULT '0',
  `zeitpunkt` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`sitzung_id`),
  KEY `benutzer_id` (`benutzer_id`),
  KEY `kategorie_id` (`kategorie_id`),
  CONSTRAINT `sitzung_ibfk_1` FOREIGN KEY (`benutzer_id`) REFERENCES `benutzer` (`benutzer_id`),
  CONSTRAINT `sitzung_ibfk_2` FOREIGN KEY (`kategorie_id`) REFERENCES `kategorie` (`kategorie_id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sitzung`
--

LOCK TABLES `sitzung` WRITE;
/*!40000 ALTER TABLE `sitzung` DISABLE KEYS */;
/*!40000 ALTER TABLE `sitzung` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Final view structure for view `frage_mit_kategorie`
--

/*!50001 DROP VIEW IF EXISTS `frage_mit_kategorie`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `frage_mit_kategorie` AS select distinct `f`.`frage_id` AS `frage_id`,`f`.`fragetext` AS `fragetext`,`f`.`erklaerung` AS `erklaerung`,`f`.`typ` AS `typ`,`k`.`kategorie_id` AS `kategorie_id`,`k`.`bezeichnung` AS `bezeichnung` from ((`frage` `f` join `frage_kategorie` `fk` on((`f`.`frage_id` = `fk`.`frage_id`))) join `kategorie` `k` on((`fk`.`kategorie_id` = `k`.`kategorie_id`))) */;
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

-- Dump completed on 2026-04-24  7:53:45
