# fedpkg --release f$$(rpm -E %fedora) local
# fedpkg --release f$(rpm -E %fedora) mockbuild --no-clean-all

Name:           nas-gui
Version:        0.0.1
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
mkdir -p %{buildroot}/%{_bindir}
install -m 755 ../../src/%{name}.py %{buildroot}/%{_bindir}/%{name}.py

mkdir -p %{buildroot}/usr/share/applications/
install -m 644 ./%{name}.desktop %{buildroot}/usr/share/applications/%{name}.desktop

mkdir -p %{buildroot}/etc/xdg/autostart/
install -m 644 ./%{name}-autostart.desktop %{buildroot}/etc/xdg/autostart/%{name}.desktop

%files
%{_bindir}/%{name}.py
/usr/share/applications/%{name}.desktop
/etc/xdg/autostart/%{name}.desktop
