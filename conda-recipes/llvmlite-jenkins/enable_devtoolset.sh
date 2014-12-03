export PATH=/opt/rh/devtoolset-2/root/usr/bin${PATH:+:${PATH}}
export MANPATH=/opt/rh/devtoolset-2/root/usr/share/man:$MANPATH
export INFOPATH=/opt/rh/devtoolset-2/root/usr/share/info${INFOPATH:+:${INFOPATH}}
export PCP_DIR=/opt/rh/devtoolset-2/root
# Some perl Ext::MakeMaker versions install things under /usr/lib/perl5
# even though the system otherwise would go to /usr/lib64/perl5.
export PERL5LIB=/opt/rh/devtoolset-2/root//usr/lib64/perl5/vendor_perl/5.8.8/x86_64-linux-thread-multi:/opt/rh/devtoolset-2/root/usr/lib/perl5:/opt/rh/devtoolset-2/root//usr/lib/perl5/vendor_perl/5.8.8${PERL5LIB:+:${PERL5LIB}}
# bz847911 workaround:
# we need to evaluate rpm's installed run-time % { _libdir }, not rpmbuild time
# or else /etc/ld.so.conf.d files?
rpmlibdir=`rpm --eval "%{_libdir}"`
# bz1017604: On 64-bit hosts, we should include also the 32-bit library path.
if [ "$rpmlibdir" != "${rpmlibdir/lib64/}" ]; then
  rpmlibdir32=":/opt/rh/devtoolset-2/root${rpmlibdir/lib64/lib}"
fi
export LD_LIBRARY_PATH=/opt/rh/devtoolset-2/root$rpmlibdir$rpmlibdir32${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
