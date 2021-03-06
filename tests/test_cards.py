# coding: utf-8

import time
from anki.db import DB
from anki.consts import *
from anki.utils import hexifyID
from tests.shared import getEmptyDeck
from anki.hooks import addHook, remHook

def test_previewCards():
    deck = getEmptyDeck()
    f = deck.newNote()
    f['Front'] = u'1'
    f['Back'] = u'2'
    # non-empty and active
    cards = deck.previewCards(f, 0)
    assert len(cards) == 1
    assert cards[0].ord == 0
    # all templates
    cards = deck.previewCards(f, 2)
    assert len(cards) == 1
    # add the note, and test existing preview
    deck.addNote(f)
    cards = deck.previewCards(f, 1)
    assert len(cards) == 1
    assert cards[0].ord == 0
    # make sure we haven't accidentally added cards to the db
    assert deck.cardCount() == 1

def test_delete():
    deck = getEmptyDeck()
    f = deck.newNote()
    f['Front'] = u'1'
    f['Back'] = u'2'
    deck.addNote(f)
    cid = f.cards()[0].id
    deck.reset()
    deck.sched.answerCard(deck.sched.getCard(), 2)
    assert deck.db.scalar("select count() from revlog") == 1
    deck.remCards([cid])
    assert deck.cardCount() == 0
    assert deck.noteCount() == 0
    assert deck.db.scalar("select count() from notes") == 0
    assert deck.db.scalar("select count() from cards") == 0
    assert deck.db.scalar("select count() from revlog") == 0
    assert deck.db.scalar("select count() from graves") == 2

def test_misc():
    d = getEmptyDeck()
    f = d.newNote()
    f['Front'] = u'1'
    f['Back'] = u'2'
    d.addNote(f)
    c = f.cards()[0]
    id = d.models.current()['id']
    assert c.template()['ord'] == 0

def test_genrem():
    d = getEmptyDeck()
    f = d.newNote()
    f['Front'] = u'1'
    f['Back'] = u''
    d.addNote(f)
    assert len(f.cards()) == 1
    m = d.models.current()
    mm = d.models
    # adding a new template should automatically create cards
    t = mm.newTemplate("rev")
    t['qfmt'] = '{{Front}}'
    t['afmt'] = ""
    mm.addTemplate(m, t)
    mm.save(m, templates=True)
    assert len(f.cards()) == 2
    # if the template is changed to remove cards, they'll be removed
    t['qfmt'] = "{{Back}}"
    mm.save(m, templates=True)
    d.remCards(d.emptyCids())
    assert len(f.cards()) == 1
    # if we add to the note, a card should be automatically generated
    f.load()
    f['Back'] = "1"
    f.flush()
    assert len(f.cards()) == 2

def test_gendeck():
    d = getEmptyDeck()
    cloze = d.models.byName("Cloze")
    d.models.setCurrent(cloze)
    f = d.newNote()
    f['Text'] = u'{{c1::one}}'
    d.addNote(f)
    assert d.cardCount() == 1
    assert f.cards()[0].did == 1
    # set the model to a new default deck
    newId = d.decks.id("new")
    cloze['did'] = newId
    d.models.save(cloze)
    # a newly generated card should share the first card's deck
    f['Text'] += u'{{c2::two}}'
    f.flush()
    assert f.cards()[1].did == 1
    # and same with multiple cards
    f['Text'] += u'{{c3::three}}'
    f.flush()
    assert f.cards()[2].did == 1
    # if one of the cards is in a different deck, it should revert to the
    # model default
    c = f.cards()[1]
    c.did = newId
    c.flush()
    f['Text'] += u'{{c4::four}}'
    f.flush()
    assert f.cards()[3].did == newId



