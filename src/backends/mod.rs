pub mod helm;

use color_eyre::eyre::Result;

pub trait Backend {
    async fn initialize(&self) -> Result<()>;
    async fn latest_version(&self) -> Result<String>;
}
