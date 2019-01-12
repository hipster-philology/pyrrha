from .base import TestModels
from app.models import AllowedMorph


class TestAllowedMorph(TestModels):
    def test_to_input_format(self):
        """ Test that export to input format works correctly """
        self.addCorpus("floovant", tokens_up_to=3, with_allowed_morph=True)
        self.assertEqual(
            AllowedMorph.to_input_format(
                AllowedMorph.query.filter(AllowedMorph.control_list == 2)
            ).replace("\r", ""),
            """label	readable
_	pas de morphologie
DEGRE=-	non applicable
MODE=imp|PERS.=2|NOMB.=p	impératif 2e personne pluriel
MODE=ind|TEMPS=psp|PERS.=3|NOMB.=s	indicatif passé simple 3e personne singulier
MODE=ind|TEMPS=pst|PERS.=1|NOMB.=s	indicatif présent 1re personne singulier
MODE=sub|TEMPS=pst|PERS.=3|NOMB.=s	subjonctif présent 3e personne singulier
NOMB.=p|GENRE=m|CAS=n	pluriel masculin nominatif
NOMB.=p|GENRE=m|CAS=r	pluriel masculin régime
NOMB.=s|GENRE=f|CAS=r	singulier féminin régime
NOMB.=s|GENRE=f|CAS=r|DEGRE=p	singulier féminin régime positif
NOMB.=s|GENRE=m|CAS=n	singulier masculin nominatif
NOMB.=s|GENRE=m|CAS=r	singulier masculin régime
PERS.=1|NOMB.=s|GENRE=m|CAS=n	1re personne singulier masculin nominatif
PERS.=2|NOMB.=p|GENRE=m|CAS=r	2e personne pluriel masculin régime
PERS.=3|NOMB.=p|GENRE=m|CAS=r	3e personne pluriel masculin régime
"""
        )
