# Password Safe
Password Safe is a password manager which integrates perfectly with the GNOME desktop and provides an easy and uncluttered interface for the management of password databases.

<img src="https://gitlab.gnome.org/World/PasswordSafe/-/raw/master/screenshots/browser.png" width="800px" />

## Features:
* ⭐ Create or import KeePass safes
* ✨ Assign a color and additional attributes to entries
* 📎 Add attachments to your encrypted database
* 🎲 Generate cryptographically strong passwords
* 🛠 Change the password or keyfile of your database
* 🔎 Quickly search your favorite entries
* 🕐 Automatic database lock during inactivity
* 📲 Adaptive interface
* ⏱ Support for two-factor authentication

### Supported Encryption Algorithms:
* AES 256-bit
* Twofish 256-bit
* ChaCha20 256-bit

### Supported Derivation algorithms:
* Argon2 KDBX4
* AES-KDF KDBX 3.1

# Installation
<a href="https://flathub.org/apps/details/org.gnome.PasswordSafe">
<img src="https://flathub.org/assets/badges/flathub-badge-i-en.png" width="190px" />
</a>

## Install Development Flatpak
Download the [latest artifact](https://gitlab.gnome.org/World/PasswordSafe/-/jobs/artifacts/master/download?job=flatpak) and extract it.
To install, open the Flatpak package with GNOME Software. Alternatively, run:
```
flatpak install org.gnome.PasswordSafe.Devel.flatpak
```

## Building locally
We use the Meson build system for. The quickest
way to get going is to run the following:
```
meson . _build
ninja -C _build
ninja -C _build install
```

## Hacking on Password Safe
To build the development version of Password Safe and hack on the code
see the [general guide](https://wiki.gnome.org/Newcomers/BuildProject)
for building GNOME apps with Flatpak and GNOME Builder.

### Translations
Helping to translate Password Safe or add support to a new language is very welcome.
You can find everything you need at: [l10n.gnome.org/module/PasswordSafe/](https://l10n.gnome.org/module/PasswordSafe/)

# Contact
You can contact through chat (Matrix protocol) on [#passwordsafe:gnome.org](https://matrix.to/#/#passwordsafe:gnome.org) channel.
