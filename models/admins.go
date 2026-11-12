package models

type Admins struct {
	AdminLogin     string `json:"admin_login"`
	AdminPassHash  string
	AdminFirstName string `json:"admin_firstname"`
	AdminLastName  string `json:"admin_lastname"`
	AdminEmail     string `json:"admin_email"`
	AdminIconUrl   string `json:"admin_iconurl"`
}

type Managers struct {
	ManagerLogin     string `json:"manager_login"`
	ManagerPassHash  string
	ManagerFirstName string `json:"manager_firstname"`
	ManagerLastName  string `json:"manager_lastname"`
	ManagerEmail     string `json:"manager_email"`
	ManagerIconUrl   string `json:"manager_iconurl"`
}
