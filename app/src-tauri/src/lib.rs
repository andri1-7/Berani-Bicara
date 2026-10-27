#[tauri::command]
fn health() -> &'static str {
    "offline-demo"
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![health])
        .run(tauri::generate_context!())
        .expect("failed to run BeraniBicara offline demo");
}

#[cfg(test)]
mod tests {
    use super::health;

    #[test]
    fn health_is_static_offline_status() {
        assert_eq!(health(), "offline-demo");
    }
}
