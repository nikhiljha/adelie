use std::{collections::HashMap, path::Path};

use color_eyre::eyre::Result;
use serde::{Deserialize, Serialize};
use toml_edit::DocumentMut;

#[derive(Debug, Serialize, Deserialize)]
pub struct Application {
    pub version: String,
    pub helm: Option<String>,
    pub chart: Option<String>,
}

pub struct VersionFile {
    pub apps: HashMap<String, Application>,
}

impl VersionFile {
    pub async fn from_file(path: impl AsRef<Path>) -> Result<VersionFile> {
        // Read the file with tokio, parse it as toml, and return the VersionFile
        let file_text = tokio::fs::read_to_string(path).await?;

        // The file is formatted like so...
        // [application_name]
        // name = "application_name"
        // version = "0.0.1"
        // helm = "helm_chart_name"
        let apps: HashMap<String, Application> = toml::from_str(&file_text)?;
        Ok(VersionFile { apps })
    }
}

pub async fn update_version(
    path: impl AsRef<Path> + Clone,
    app: &str,
    version: &str,
    commit: bool,
) -> Result<()> {
    // Read the file with tokio, parse it as toml, update the version, and write it back
    // use toml-edit to preserve style
    let file_text = tokio::fs::read_to_string(path.clone()).await?;
    let mut doc: DocumentMut = file_text.parse()?;
    let old_version = doc[app]["version"].as_str().unwrap().to_string();
    doc[app]["version"] = toml_edit::value(version);
    let new_file = doc.to_string();
    tokio::fs::write(path.clone(), new_file).await?;

    // If commit is true, use git2 to commit the change
    if commit {
        let canonical_path = std::fs::canonicalize(path.clone())?;
        let repo = git2::Repository::discover(canonical_path.parent().unwrap())?;
        let mut index = repo.index()?;

        // Get the file path relative to repo root
        let relative_file_path = canonical_path.strip_prefix(repo.workdir().unwrap())?;

        index.add_path(&relative_file_path.as_ref())?;
        index.write()?;
        let tree_id = index.write_tree()?;
        let tree = repo.find_tree(tree_id)?;
        let head = repo.head()?;
        let parent = repo.find_commit(head.peel_to_commit()?.id())?;
        let sig = repo.signature()?;
        let message = format!(
            ":arrow_up: {}: {} -> {}\n\nThis commit was automatically created by Adelie <https://github.com/nikhiljha/adelie>.",
            app, 
            old_version,
            version,
        );
        repo.commit(Some("HEAD"), &sig, &sig, &message, &tree, &[&parent])?;
    }

    Ok(())
}
