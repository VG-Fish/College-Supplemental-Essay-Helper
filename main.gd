extends Control

@onready var http_request: HTTPRequest = $HTTPRequest
const url: String = "https://vgfishy.pythonanywhere.com/gemini?prompt=%s"
var response: String
var chat_history: Array[String] = []

func _ready() -> void:
	$HTTPRequest.request_completed.connect(_on_request_completed)
	$PanelContainer/VBoxContainer/Answer.custom_minimum_size.x = get_viewport_rect().size.x
	chat_history.append("System Context: Do NOT respond in markdown and use plain text. If annotated with User, whatever after the colon is the question that YOU must respond too. %s" % $PanelContainer/VBoxContainer/Info.text)

func _on_request_completed(_result, _response_code, _headers, body) -> void:
	if not body:
		return
	
	var json: Dictionary = JSON.parse_string(body.get_string_from_utf8())
	if json["candidates"][0].get("content", ""):
		response = json["candidates"][0]["content"]["parts"][0]["text"].replace("\n", "")
		$PanelContainer/VBoxContainer/Answer.text = response
		chat_history.append("System: %s" % response)
	
func _on_line_edit_text_submitted(prompt: String) -> void:
	chat_history.append("User : %s" % prompt)
	$HTTPRequest.request((url % " ".join(chat_history)).replace(" ", "%20"))
	$PanelContainer/VBoxContainer/LineEdit.text = ""
