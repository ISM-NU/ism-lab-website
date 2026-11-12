package models

import "time"

type Message struct {
	MessageTitle   string   `json:"message_title"`
	MessageContent string   `json:"message_content"`
	AdditionalInfo MetaData `json:"meta_data"`
}

type MetaData struct {
	AppliedMethod      string    `json:"applied_method"`
	TargetRoute        string    `json:"target_route"`
	ResponseServerTime time.Time `json:"response_server_time"`
}

type Photo struct {
	PhotoURL         string `json:"photo_url"`
	PhotoID          int    `json:"photo_id"`
	PhotoDescription string `json:"photo_description"`
	Photo            []byte `json:"photo"`
}

type UploadPhotoData struct {
	Description string `json:"photo_description"`
	Photo       []byte `json:"photo"`
}

type ReturnPhotoData struct {
	PhotoURL string `json:"photo_url"`
}

type CurrentlyOnlineUsers struct {
	UserLogin     string `json:"user_login"`
	UserRole      string `json:"user_role"`
	IsCurrentUser bool   `json:"current_session"`
}

type EventsData struct {
	EventID                string    `json:"event_id"`
	EventTitle             string    `json:"event_title"`
	EventPlace             string    `json:"event_place"`
	EventStartDate         time.Time `json:"event_start_date"`
	EventStartTime         time.Time `json:"event_start_time"`
	EventFinishDate        time.Time `json:"event_finish_date"`
	EventFinishTime        time.Time `json:"event_finish_time"`
	EventDescription       string    `json:"event_description"`
	RegistrationLink       string    `json:"registration_link"`
	AnnouncementDate       time.Time `json:"announcement_date"`
	AnnouncementTime       time.Time `json:"announcement_time"`
	RegistrationFinishDate time.Time `json:"registration_finish_date"`
	RegistrationFinishTime time.Time `json:"registration_finish_time"`
}

type ReturnEventID struct {
	EventID string `json:"event_id"`
}

type ParticipantData struct {
	ParticipantID  string `json:"participant_id"`
	FirstName      string `json:"first_name"`
	LastName       string `json:"last_name"`
	MiddleName     string `json:"middle_name"`
	Organization   string `json:"organization"`
	AttendingEvent string `json:"attending_event"`
}

type MemberData struct {
	MemberID              int64     `json:"member_id"`
	FirstName             string    `json:"first_name"`
	LastName              string    `json:"last_name"`
	CurrentYearOfStudy    int64     `json:"current_year_of_study"`
	CurrentlyStudying     string    `json:"currently_studying"`
	Degree                string    `json:"degree"`
	JoinDate              time.Time `json:"join_date"`
	AdditionalDescription string    `json:"additional_description"`
	MemberIcon            string    `json:"member_icon"`
	Email                 string    `json:"email"`
}

type ProjectData struct {
	ProjectID          int64  `json:"project_id"`
	ProjectName        string `json:"project_name"`
	ProjectDescription string `json:"project_description"`
}

type Announcements struct {
	AnnouncementID          int64     `json:"announcement_id"`
	AnnouncementTitle       string    `json:"announcement_title"`
	AnnouncementDescription string    `json:"announcement_description"`
	AnnouncementDate        time.Time `json:"announcement_date"`
	AnnouncementTime        time.Time `json:"announcement_time"`
}

type Publications struct {
	PublicationID       int64    `json:"publication_id"`
	PublicationTitle    string   `json:"publication_title"`
	PublicationKeywords []string `json:"publication_keywords"`
	DOI                 string   `json:"doi"`
}

type Datasets struct {
	DataID          int64     `json:"data_id"`
	DataName        string    `json:"data_name"`
	DataType        string    `json:"data_type"`
	DataDescription string    `json:"data_description"`
	Date            time.Time `json:"data_date"`
	Version         int64     `json:"data_version"`
	Size            float64   `json:"data_size"`
	Format          string    `json:"data_format"`
}
