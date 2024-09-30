//! This module contains the CLI to search for a wheel on PyPI.
//! using your project's configuration.
use crate::Project;

use super::cli_config::ProjectConfig;
use clap::Parser;
use miette::{Context, IntoDiagnostic};
use pep508_rs::PackageName;
use pixi_config::get_cache_dir;
use pixi_consts::consts;
use pixi_utils::reqwest::build_reqwest_clients;
use rattler_conda_types::Platform;
use uv_client::RegistryClientBuilder;

/// Search for a package on one or multiple PyPI indexes.
///
/// Its output will list the latest version of package.
#[derive(Debug, Parser)]
#[clap(arg_required_else_help = true)]
pub struct Args {
    /// Name of package to search
    #[arg(required = true)]
    pub package: String,

    /// The platform to search for, defaults to current platform
    #[arg(short, long, default_value_t = Platform::current())]
    pub platform: Platform,

    /// Limit the number of search results
    #[clap(short, long)]
    limit: Option<usize>,

    #[clap(flatten)]
    pub project_config: ProjectConfig,
}

fn create_uv_cache() -> miette::Result<uv_cache::Cache> {
    let uv_cache = get_cache_dir()?.join(consts::PYPI_CACHE_DIR);
    if !uv_cache.exists() {
        std::fs::create_dir_all(&uv_cache)
            .into_diagnostic()
            .context("failed to create uv cache directory")?;
    }

    let cache = uv_cache::Cache::from_path(uv_cache);
    Ok(cache)
}

pub async fn execute(args: Args) -> miette::Result<()> {
    // TODO:
    // 1. Use the project configuration for the VersionMap
    // 2. Show the available wheels for this package, display a message if there are no wheels available and they might be filtered out
    // 3. Show only the wheels for this version when the version is specified
    // 4. Figure out the best way to show the Archived name and version without using the version map

    let cache = create_uv_cache().wrap_err("error setting up uv cache")?;

    let project = Project::load_or_else_discover(args.project_config.manifest_path.as_deref()).ok();

    let reqwest_client = project
        .as_ref()
        .map(|p| p.client().clone())
        .unwrap_or_else(|| build_reqwest_clients(None).0);

    let client = RegistryClientBuilder::new(cache)
        .client(reqwest_client)
        .connectivity(uv_client::Connectivity::Online)
        .build();
    let package_name = PackageName::new(args.package.clone()).into_diagnostic()?;
    let results = client.simple(&package_name).await.into_diagnostic()?;

    // Print the results
    for (index, metadata) in results.iter().take(args.limit.unwrap_or(results.len())) {
        for metadata in metadata.iter() {
            metadata.files.wheels.iter().for_each(|wheel| {
                wheel.name.deserialise().unwrap();
                println!("{} {}", wheel.name.name.as_str(), wheel.name.version);
            });
        }
    }

    Ok(())
}
