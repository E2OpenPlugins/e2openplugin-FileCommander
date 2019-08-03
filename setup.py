from distutils.core import setup
import setup_translate

pkg = 'Extensions.FileCommander'
setup (name = 'enigma2-plugin-extensions-filecommander',
       version = '1.0.0',
       description = 'File manager based on OpenATV one',
       packages = [pkg],
       package_dir = {pkg: 'plugin'},
       package_data = {pkg: ['*.png', '*.xml', '*/*.png', 'locale/*/LC_MESSAGES/*.mo']},
       cmdclass = setup_translate.cmdclass, # for translation
      )
