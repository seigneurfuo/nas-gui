# fedpkg --release f39 local
# fedpkg --release f39 mockbuild --no-clean-all

Name:           nas-gui
Version:        2024.05.01
Release:        %autorelease
BuildArch:      noarch
Summary:        A nsi

License:        None
URL:            .

Requires:       python3
Requires:       python3-PyQt6

%description
Un programme qui permet de monter les partages réseaux du NAS depuis la zone de notification

%install
# Programme
mkdir -p %{buildroot}/%{_bindir}
install -m 755 ../../src/%{name}.py %{buildroot}/%{_bindir}/%{name}.py

# Changelog
mkdir -p %{buildroot}/usr/share/%{name}
install -m 644 ../../src/changelog.txt %{buildroot}/usr/share/%{name}/changelog.txt

# Racourci
mkdir -p %{buildroot}/usr/share/applications/
install -m 644 ./%{name}.desktop %{buildroot}/usr/share/applications/%{name}.desktop

# Autostart
mkdir -p %{buildroot}/etc/xdg/autostart/
install -m 644 ./%{name}-autostart.desktop %{buildroot}/etc/xdg/autostart/%{name}.desktop

%files
%{_bindir}/%{name}.py
/usr/share/%{name}/changelog.txt
/usr/share/applications/%{name}.desktop
/etc/xdg/autostart/%{name}.desktop
