
CREATE TABLE IF NOT EXISTS Photo (
    PhotoURL TEXT PRIMARY KEY,
    PhotoID SERIAL UNIQUE,
    PhotoDescription TEXT,
    Photo BYTEA
);

CREATE TABLE IF NOT EXISTS Administrator (
    AdminLogin TEXT PRIMARY KEY,
    AdminPassHash TEXT NOT NULL,
    AdminFirstName TEXT NOT NULL,
    AdminLastName TEXT NOT NULL,
    AdminEmail TEXT UNIQUE NOT NULL,
    AdminIcon TEXT,
    CONSTRAINT fk_admin_icon
        FOREIGN KEY (AdminIcon)
        REFERENCES Photo(PhotoURL)
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS Manager (
    MngLogin TEXT PRIMARY KEY,
    MngPassHash TEXT NOT NULL,
    MngFirstName TEXT NOT NULL,
    MngLastName TEXT NOT NULL,
    MngEmail TEXT UNIQUE NOT NULL,
    MngIcon TEXT,
    CONSTRAINT fk_manager_icon
        FOREIGN KEY (MngIcon)
        REFERENCES Photo(PhotoURL)
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS Sessions (
    SessionID TEXT PRIMARY KEY,
    UserLogin TEXT NOT NULL,
    UserRole TEXT NOT NULL CHECK (UserRole IN ('Administrator', 'Manager')),
    LoggedInTime TIME,
    LoggedInDate DATE,
    LoggedOutTime TIME,
    LoggedOutDate DATE,
    SessionStatus TEXT,
    CONSTRAINT fk_session_admin
        FOREIGN KEY (UserLogin)
        REFERENCES Administrator(AdminLogin)
        ON DELETE CASCADE,
    CONSTRAINT fk_session_manager
        FOREIGN KEY (UserLogin)
        REFERENCES Manager(MngLogin)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Events (
    EventID TEXT PRIMARY KEY,
    EventTitle TEXT NOT NULL,
    EventPlace TEXT,
    EventStartDate DATE,
    EventStartTime TIME,
    EventFinishDate DATE,
    EventFinishTime TIME,
    Description TEXT,
    RegistrationLink TEXT,
    AnnouncementDate DATE,
    AnnouncementTime TIME,
    RegistrationFinishDate DATE,
    RegistrationFinishTime TIME
);

CREATE TABLE IF NOT EXISTS ListsOfParticipants (
    ParticipantID SERIAL PRIMARY KEY,
    FirstName TEXT NOT NULL,
    LastName TEXT NOT NULL,
    MiddleName TEXT,
    Organization TEXT,
    AttendingEvent TEXT,
    CONSTRAINT fk_participant_event
        FOREIGN KEY (AttendingEvent)
        REFERENCES Events(EventID)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ISMLabMembers (
    MemberID SERIAL PRIMARY KEY,
    FirstName TEXT NOT NULL,
    LastName TEXT NOT NULL,
    CurrentYearOfStudy INTEGER,
    CurrentlyStudying TEXT,
    Degree TEXT,
    JoinDate DATE,
    AdditionalDescription TEXT,
    MemberIcon TEXT,
    Email TEXT UNIQUE,
    CONSTRAINT fk_member_icon
        FOREIGN KEY (MemberIcon)
        REFERENCES Photo(PhotoURL)
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS Projects (
    ProjectID SERIAL PRIMARY KEY,
    ProjectName TEXT NOT NULL,
    ProjectDescription TEXT
);

CREATE TABLE IF NOT EXISTS Announcements (
    AnnouncementID SERIAL PRIMARY KEY,
    AnnouncementTitle TEXT NOT NULL,
    AnnouncementDescription TEXT,
    AnnouncementDate DATE,
    AnnouncementTime TIME
);

CREATE TABLE IF NOT EXISTS Publications (
    PublicationID SERIAL PRIMARY KEY,
    PublicationTitle TEXT NOT NULL,
    PublicationKeywords TEXT[],
    DOI TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS Datasets (
    DataID SERIAL PRIMARY KEY,
    Name TEXT NOT NULL,
    Type TEXT,
    Description TEXT,
    Date TEXT,
    Version INTEGER,
    Size DOUBLE PRECISION,
    Format TEXT
);