use std::{borrow::Borrow, str::FromStr};

use pep440_rs::VersionSpecifiers;
use pep508_rs::{InvalidNameError, PackageName};
use serde::{Deserialize, Deserializer, Serialize, Serializer};
use uv_git::GitReference;

#[derive(Debug, Clone, Eq, PartialEq, Hash)]
/// A package name for PyPI that also stores the source version of the name.
pub struct PyPiPackageName {
    source: String,
    normalized: PackageName,
}

impl Borrow<PackageName> for PyPiPackageName {
    fn borrow(&self) -> &PackageName {
        &self.normalized
    }
}

impl<'de> Deserialize<'de> for PyPiPackageName {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        serde_untagged::UntaggedEnumVisitor::new()
            .string(|str| PyPiPackageName::from_str(str).map_err(serde::de::Error::custom))
            .expecting("a string")
            .deserialize(deserializer)
    }
}

impl FromStr for PyPiPackageName {
    type Err = InvalidNameError;

    fn from_str(name: &str) -> Result<Self, Self::Err> {
        Ok(Self {
            source: name.to_string(),
            normalized: uv_normalize::PackageName::from_str(name)?,
        })
    }
}

impl PyPiPackageName {
    pub fn from_normalized(normalized: PackageName) -> Self {
        Self {
            source: normalized.to_string(),
            normalized,
        }
    }

    pub fn as_normalized(&self) -> &PackageName {
        &self.normalized
    }

    pub fn as_source(&self) -> &str {
        &self.source
    }
}

/// The pep crate does not support "*" as a version specifier, so we need to
/// handle it ourselves.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum VersionOrStar {
    Version(VersionSpecifiers),
    Star,
}

impl FromStr for VersionOrStar {
    type Err = pep440_rs::VersionSpecifiersParseError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        if s == "*" {
            Ok(VersionOrStar::Star)
        } else {
            Ok(VersionOrStar::Version(VersionSpecifiers::from_str(s)?))
        }
    }
}

impl ToString for VersionOrStar {
    fn to_string(&self) -> String {
        match self {
            VersionOrStar::Version(v) => v.to_string(),
            VersionOrStar::Star => "*".to_string(),
        }
    }
}

impl From<VersionOrStar> for Option<pep508_rs::VersionOrUrl> {
    fn from(val: VersionOrStar) -> Self {
        match val {
            VersionOrStar::Version(v) => Some(pep508_rs::VersionOrUrl::VersionSpecifier(v)),
            VersionOrStar::Star => None,
        }
    }
}

impl From<VersionOrStar> for VersionSpecifiers {
    fn from(value: VersionOrStar) -> Self {
        match value {
            VersionOrStar::Version(v) => v,
            VersionOrStar::Star => VersionSpecifiers::empty(),
        }
    }
}

impl Serialize for VersionOrStar {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_str(&self.to_string())
    }
}

impl<'de> Deserialize<'de> for VersionOrStar {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        let s = String::deserialize(deserializer)?;
        VersionOrStar::from_str(&s).map_err(serde::de::Error::custom)
    }
}

#[derive(Debug, Serialize, Clone, PartialEq, Eq, Hash)]
#[serde(untagged, rename_all = "snake_case", deny_unknown_fields)]
pub enum GitRev {
    Short(String),
    Full(String),
}

impl GitRev {
    pub fn as_full(&self) -> Option<&str> {
        match self {
            GitRev::Full(full) => Some(full.as_str()),
            GitRev::Short(_) => None,
        }
    }

    pub fn to_git_reference(&self) -> GitReference {
        match self {
            GitRev::Full(rev) => GitReference::FullCommit(rev.clone()),
            GitRev::Short(rev) => GitReference::BranchOrTagOrCommit(rev.clone()),
        }
    }
}

impl From<&str> for GitRev {
    fn from(s: &str) -> Self {
        if s.len() == 40 {
            GitRev::Full(s.to_string())
        } else {
            GitRev::Short(s.to_string())
        }
    }
}

impl ToString for GitRev {
    fn to_string(&self) -> String {
        match self {
            GitRev::Short(s) => s.clone(),
            GitRev::Full(s) => s.clone(),
        }
    }
}

impl<'de> Deserialize<'de> for GitRev {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        let s: String = Deserialize::deserialize(deserializer)?;
        if s.len() == 40 {
            Ok(GitRev::Full(s))
        } else {
            Ok(GitRev::Short(s))
        }
    }
}
