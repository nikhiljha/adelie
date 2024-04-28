mod backends;
mod frontend;

use backends::Backend;
use clap::Parser;
use color_eyre::eyre::Result;
use url::Url;

#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
struct Args {
    /// file to read
    #[arg(short, long)]
    file: String,

    /// application to update/check
    #[arg(short, long)]
    app: Option<String>,

    /// whether to update the version or just check
    #[arg(short, long)]
    update: bool,

    /// whether to commit the change
    #[arg(short, long)]
    commit: bool,
}

#[tokio::main]
async fn main() -> Result<()> {
    color_eyre::install()?;

    // Parse the command line arguments
    let args = Args::parse();

    // Load the file as VersionFile
    let version_file = frontend::VersionFile::from_file(&args.file).await?;

    // For each app, use available backends to get the latest version
    for (name, app) in version_file.apps.iter() {
        if args.app.is_none() || args.app.as_ref().unwrap() == name {
            println!("Checking {}...", name);
            if app.helm.is_some() {
                let repo_url = app.helm.as_ref().unwrap();
                // If there's no trailing slash, add one
                let repo_url = if repo_url.ends_with('/') {
                    repo_url.to_string()
                } else {
                    format!("{}/", repo_url)
                };
                let helm = backends::helm::Helm::new(
                    Url::parse(&repo_url)?,
                    app.chart.as_ref().unwrap_or_else(|| &name).to_string(),
                );
                helm.initialize().await?;
                let latest_version = helm.latest_version().await?;
                // Trim a leading "v" if it exists
                let latest_version = latest_version.trim_start_matches('v');
                if latest_version == app.version {
                    println!("✅ {}: up to date", name);
                } else {
                    println!("⬆️ {}: {} -> {}", name, app.version, latest_version);
                    if args.update {
                        frontend::update_version(&args.file, name, &latest_version, args.commit).await?;
                    }
                }
            }
        }
    }

    Ok(())
}
