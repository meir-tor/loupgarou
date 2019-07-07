
RE_AGENT_GROUP  = '(Agent\[(?P<id>\d\d)\])'
RE_AGENT        = '(Agent\[\d\d\])'


RE_SUBJECT      = '(?P<subject>{RE_AGENT}|ANY)'.format(**locals()) # Can be omitted
RE_TARGET       = '(?P<target>{RE_AGENT}|ANY)'.format(**locals())
RE_ROLE         = '(?P<role>VILLAGER|SEER|MEDIUM|BODYGUARD|WEREWOLF|POSSESSED|ANY)'
RE_SPECIES      = '(?P<species>HUMAN|WEREWOLF|ANY)'
RE_TALK_NUMBER  = '(?P<talk_number>/d+)'

RE_ESTIMATE     = '({RE_SUBJECT} )?ESTIMATE {RE_TARGET} {RE_ROLE}'.format(**locals())
RE_COMINGOUT    = '({RE_SUBJECT} )?COMINGOUT {RE_TARGET} {RE_ROLE}'.format(**locals())

RE_DIVINATION   = '({RE_SUBJECT} )?DIVINATION {RE_TARGET}'.format(**locals())
RE_GUARD        = '({RE_SUBJECT} )?GUARD {RE_TARGET}'.format(**locals())
RE_VOTE         = '({RE_SUBJECT} )?VOTE {RE_TARGET}'.format(**locals())
RE_ATTACK       = '({RE_SUBJECT} )?ATTACK {RE_TARGET}'.format(**locals())

RE_DIVINED      = '({RE_SUBJECT} )?DIVINED {RE_TARGET} {RE_SPECIES}'.format(**locals())
RE_IDENTIFIED   = '({RE_SUBJECT} )?IDENTIFIED {RE_TARGET} {RE_SPECIES}'.format(**locals())
RE_GUARDED      = '({RE_SUBJECT} )?GUARDED {RE_TARGET}'.format(**locals())
RE_VOTED        = '({RE_SUBJECT} )?VOTED {RE_TARGET}'.format(**locals())
RE_ATTACKED     = '({RE_SUBJECT} )?ATTACKED {RE_TARGET}'.format(**locals())

RE_AGREE        = '({RE_SUBJECT} )?AGREE {RE_TALK_NUMBER}'.format(**locals())
RE_DISAGREE     = '({RE_SUBJECT} )?DISAGREE {RE_TALK_NUMBER}'.format(**locals())

RE_OVER         = 'OVER'
RE_SKIP         = 'SKIP'


RE_REQUEST      = '({RE_SUBJECT} )?REQUEST {RE_TARGET} \((.*)\)'.format(**locals())
RE_INQUIRE      = '({RE_SUBJECT} )?INQUIRE {RE_TARGET} \((.*)\)'.format(**locals())
RE_BECAUSE      = '({RE_SUBJECT} )?BECAUSE \((.*)\) \((.*)\)'.format(**locals())

RE_DAY_NUMBER   = '(?P<day>/d)'
RE_DAY          = '({RE_SUBJECT} )?DAY {RE_DAY_NUMBER} \(.*\)'.format(**locals())

RE_NOT          = '({RE_SUBJECT} )?NOT \(.*\)'.format(**locals())
RE_AND          = '({RE_SUBJECT} )?AND (.*)'.format(**locals())
RE_OR           = '({RE_SUBJECT} )?OR (.*)'.format(**locals())
RE_XOR          = '({RE_SUBJECT} )?XOR \(.*\) \(.*\)'.format(**locals())
