package models

type MainPagePrinter struct {
	CurrentYear int
}

type ErrorPage struct {
	ErrorCode       int
	OfficialMessage string
	Explanation     string
}
